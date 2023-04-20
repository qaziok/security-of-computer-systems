import os
import queue
import socket
import threading

from Crypto.Random import get_random_bytes

from projekt.app.gui.gui_actions import GuiActions
from projekt.functional.communication import UserActions
from projekt.functional.communication.sockets import RSASocket, AESSocket
from projekt.functional.encryption import Keys

CHUNK_SIZE = 750


class UserManager:
    def __init__(self, keys, *, users_controller):
        self.user_id = None
        self.sender = None
        self.connected = None
        self.conn = None
        self.user_keys = None
        self.sending_condition = threading.Condition()
        self.users_controller = users_controller
        self.server_keys = keys
        self.messages_to_send = queue.Queue()
        self.files_buffer = {}
        self.files_flag = {}

    # two modes: server and client
    # server mode: we are waiting for connection from other user
    # client mode: we are asking for connection from other user

    def create_connection(self, **kwargs):
        if not (kwargs.get('data') or (kwargs.get('conn') and kwargs.get('addr'))):
            raise ValueError("Invalid arguments")

        if kwargs.get('data'):
            addr = self.__client(kwargs.get('data'))
        else:
            addr = self.__server(kwargs.get('conn'), kwargs.get('addr'))

        self.connected = True
        return addr

    def __server(self, conn, addr):
        self.conn = conn

        self.rsa_socket = RSASocket(self.conn, self.server_keys.private_key, None)
        code = self.rsa_socket.recv()
        user_info = self.users_controller.find_user(code)
        self.user_id = user_info.get('user_id')

        self.user_keys = Keys.import_keys(public_key=user_info.get('public_key'))
        self.rsa_socket = RSASocket(self.conn, self.server_keys.private_key, self.user_keys.public_key)

        self.session_key = get_random_bytes(32)

        self.rsa_socket.send(self.session_key)

        self.aes_socket = AESSocket(self.conn, self.session_key)

        return user_info.get('user_id'), addr

    def __client(self, data):
        self.user_id = data.get('user_id')
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(data.get('connection_address'))
        self.user_keys = Keys.import_keys(public_key=data.get('public_key'))

        self.rsa_socket = RSASocket(self.conn, self.server_keys.private_key, self.user_keys.public_key)

        self.rsa_socket.send(data.get('find_code'))

        self.session_key = self.rsa_socket.recv()

        self.aes_socket = AESSocket(self.conn, self.session_key)

        return data.get('user_id'), data.get('connection_address')

    def close(self):
        self.connected = False
        self.conn.close()
        self.sender.join()

    def send(self, *, action=None, **data):
        data['action'] = action
        self.messages_to_send.put(data)

    def __send(self, data):
        self.aes_socket.send(data)

    def recv(self):
        return self.aes_socket.recv()

    def connection(self):
        self.sender = threading.Thread(target=self.__sender)
        self.sender.start()

        while self.connected:
            data = self.recv()
            if not data:
                continue

            self.__handle(data)

    def __handle(self, data):
        match data.get('action'):
            case UserActions.MESSAGE:
                self.__notify_gui(data)
            case UserActions.DOWNLOAD_FILE:
                self.__send_file(data)
            case UserActions.FILE_HEADER:
                self.__handle_file_header(data)
            case UserActions.FILE:
                self.__handle_file(data)
            case UserActions.NEXT_CHUNK:
                with self.files_flag[data.get('file_id')]:
                    self.files_flag[data.get('file_id')].notify()

    def __send_file(self, data):
        file_id = data.get('file_id')
        self.files_flag[file_id] = threading.Condition()
        file_path = self.users_controller.downloadable_files.get(file_id)

        with open(file_path, 'rb') as file:
            nonce, encrypted_file, tag = self.aes_socket.aes_translator.encrypt(file.read())

        self.send(
            action=UserActions.FILE_HEADER,
            nonce=nonce,
            tag=tag,
            file_id=file_id,
            file_name=os.path.basename(file_path),
            file_size=len(encrypted_file),
            number_of_chunks=len(encrypted_file) // CHUNK_SIZE + 1
        )

        def __send_file_chunk():
            for i in range(0, len(encrypted_file), CHUNK_SIZE):
                chunk = encrypted_file[i:i + CHUNK_SIZE]
                while True:
                    self.send(action=UserActions.FILE, file_id=file_id, file_chunk=chunk, chunk_number=i // CHUNK_SIZE)
                    with self.files_flag[file_id]:
                        if self.files_flag[file_id].wait(timeout=1):
                            break

        threading.Thread(target=__send_file_chunk).start()

    def __handle_file_header(self, data):
        self.files_buffer[data.get('file_id')] = {
            **data, 'file_buffer': {}
        }
        self.__notify_gui({
            'action': UserActions.FILE_HEADER,
            'file_id': data.get('file_id'),
            'file_name': data.get('file_name'),
            'number_of_chunks': data.get('number_of_chunks')
        })

    def __handle_file(self, data):
        file = self.files_buffer[data.get('file_id')]
        file['file_buffer'].update({data.get('chunk_number'): data.get('file_chunk')})

        print(f"Received chunk {data.get('chunk_number') + 1} of {file['number_of_chunks']}")
        self.send(action=UserActions.NEXT_CHUNK, file_id=data.get('file_id'), chunk_number=data.get('chunk_number'))
        self.__notify_gui({
            'action': UserActions.FILE_PROGRESS,
            'file_id': data.get('file_id'),
            'progress': len(file['file_buffer'])
        })

        # validate if all chunks were received
        if len(file['file_buffer']) == file['number_of_chunks']:
            encrypted_file = b''.join([file['file_buffer'][x] for x in range(file['number_of_chunks'])])

            if len(encrypted_file) != file['file_size']:
                print("File corrupted")
                return

            decrypted_file = self.aes_socket.aes_translator.decrypt(
                file['nonce'], encrypted_file, file['tag']
            )
            print(len(decrypted_file))
            # save file
            with open(os.path.join(".", "downloads", file['file_name']), 'wb') as f:
                f.write(decrypted_file)

            del self.files_buffer[data.get('file_id')]

    def __notify_gui(self, data):
        data['user_id'] = self.user_id
        data['action'] = GuiActions.translate(data.get('action'))
        self.users_controller.gui.notify(data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __sender(self):
        while self.connected:
            if not self.messages_to_send.empty():
                message = self.messages_to_send.get()
                self.__send(message)
