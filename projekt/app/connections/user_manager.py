import os
import queue
import socket
import threading

from Crypto.Random import get_random_bytes

from projekt.app.gui.gui_actions import GuiActions
from projekt.functional.communication import UserActions
from projekt.functional.communication.sockets import RSASocket, AESSocket, FileSocket
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

        self.rsa_socket.send(self.users_controller.encryption.encode('ascii'))
        user_encryption = self.rsa_socket.recv().decode('ascii')

        self.aes_socket = AESSocket(self.conn, self.session_key). \
            change_sending_encryption(self.users_controller.encryption). \
            change_receiving_encryption(user_encryption)

        return user_info.get('user_id'), addr

    def __client(self, data):
        self.user_id = data.get('user_id')
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(data.get('connection_address'))
        self.user_keys = Keys.import_keys(public_key=data.get('public_key'))

        self.rsa_socket = RSASocket(self.conn, self.server_keys.private_key, self.user_keys.public_key)

        self.rsa_socket.send(data.get('find_code'))

        self.session_key = self.rsa_socket.recv()

        self.rsa_socket.send(self.users_controller.encryption.encode('ascii'))
        user_encryption = self.rsa_socket.recv().decode('ascii')

        self.aes_socket = AESSocket(self.conn, self.session_key). \
            change_sending_encryption(self.users_controller.encryption). \
            change_receiving_encryption(user_encryption)

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

        try:
            while self.connected:
                data = self.recv()
                if not data:
                    continue

                self.__handle(data)
        except (ConnectionResetError, ConnectionAbortedError):
            self.close()

    def __handle(self, data):
        match data.get('action'):
            case UserActions.MESSAGE:
                self.__notify_gui(data)
            case UserActions.DOWNLOAD_FILE:
                threading.Thread(target=self.__send_file, args=(data,)).start()
            case UserActions.CHANGED_ENCRYPTION:
                self.aes_socket.change_receiving_encryption(data.get('encryption'))

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

    def change_encryption(self, encryption):
        self.__send({
            'action': UserActions.CHANGED_ENCRYPTION,
            'encryption': encryption
        })
        self.aes_socket.change_sending_encryption(encryption)

    def __send_file(self, data):
        file_id = data.get('file_id')
        file_path = self.users_controller.downloadable_files.get(file_id)

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(data.get('channel'))

        aes_socket = self.aes_socket.copy(conn, self.session_key)

        aes_socket.send({
            'action': UserActions.FILE_HEADER,
            'file_id': file_id,
            'file_name': os.path.basename(file_path)
        })

        with open(file_path, 'rb') as file:
            file_socket = FileSocket(conn, self.session_key). \
                change_sending_encryption(self.aes_socket.sending_encryption)

            file_socket.send(file.read())

        conn.close()

    def __update_progress_bar(self, file_id, downloaded):
        self.__notify_gui({
            'action': UserActions.FILE_PROGRESS,
            'file_id': file_id,
            'progress': int(downloaded)
        })

    def __download_file(self, channel, file_id):
        conn, addr = channel.accept()
        aes_socket = self.aes_socket.copy(conn, self.session_key)

        file_info = aes_socket.recv()
        self.__notify_gui(file_info)

        file_socket = FileSocket(conn, self.session_key). \
            change_receiving_encryption(self.aes_socket.receiving_encryption)

        file = file_socket.recv(lambda p: self.__update_progress_bar(file_id, p))

        with open(os.path.join(".", "downloads", file_info.get('file_name')), 'wb') as f:
            f.write(file)

        self.__notify_gui({
            'action': UserActions.FILE_DOWNLOADED,
            'file_id': file_id
        })

        conn.close()

    def download_file(self, channel, file_id):
        self.send(
            action=UserActions.DOWNLOAD_FILE,
            file_id=file_id,
            channel=channel.getsockname()
        )
        threading.Thread(target=self.__download_file, args=(channel, file_id)).start()
