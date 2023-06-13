import logging
import socket
import threading
from queue import Queue

from Crypto.Random import get_random_bytes

from projekt.app.gui.gui_actions import GuiActions
from projekt.functional.communication.sockets import RSASocket
from projekt.functional.communication.sockets.aes_socket import AESSocket
from projekt.functional.encryption import Keys
from projekt.functional.communication import ClientActions, ServerActions

KEEP_ALIVE_TIMER = 30


class ServerManager:
    def __init__(self, host, port, users_controller):
        self.users_controller = users_controller
        self.gui = None
        self.__active_users = {}
        self.connected = False
        self.socket = None
        self.__user_info = {}
        self.server_address = (host, port)
        self.user_keys = None
        self.session_key = get_random_bytes(32)
        self.active_threads = []
        self.tasks_to_gui = Queue()
        self.tasks_lock = threading.Lock()
        self.task_added = threading.Condition()
        self.shutdown_condition = threading.Condition()
        self.active_users_condition = threading.Condition()
        self.__user_info_lock = threading.Lock()

    def start(self, user, keys):
        self.__load(user, keys)
        self.__handshake()
        self.__connection()

    def stop(self):
        self.__leave()

    def __load(self, user, keys):
        self.user_keys = keys
        with self.__user_info_lock:
            self.__user_info.update({
                "name": user,
                "status": "Hello World!",
                'connection_address': self.users_controller.connection_address()
            })

    def __handshake(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.server_address)

        self.socket.sendall(self.user_keys.public_key.exportKey())

        self.server_keys = Keys.import_keys(public_key=self.socket.recv(1024))

        self.rsa_socket = RSASocket(self.socket, self.user_keys.private_key, self.server_keys.public_key)

        self.rsa_socket.send(self.session_key)

        self.aes_socket = AESSocket(self.socket, self.session_key)

        self.send(**self.__user_info)

        self.connected = True

    def __leave(self):
        if self.connected:
            self.send(action=ClientActions.LEAVE)

        self.connected = False
        with self.shutdown_condition:
            self.shutdown_condition.notify_all()

        for thread in self.active_threads:
            thread.join()

        if self.socket is not None:
            self.socket.close()

    def send(self, *, action=None, **data):
        data['action'] = action
        self.aes_socket.send(data)

    def recv(self):
        return self.aes_socket.recv()

    def __keep_alive(self):
        while self.connected:
            with self.shutdown_condition:
                self.send(action=ClientActions.ACTIVE)
                self.shutdown_condition.wait(timeout=KEEP_ALIVE_TIMER)

    def __receiver(self):
        while self.connected:
            data = self.recv()
            if data is not None:
                self.__handle(data)

    def __handle(self, data):
        match data.get("action"):
            case (ServerActions.ASK_USER_FOR_CONNECTION
                  | ServerActions.CONNECTION_REJECTED
                  | ServerActions.ACTIVE_USERS):
                self.__notify_user(data)
            case ServerActions.CONNECTION_APPROVED:
                self.users_controller.add_user(data)
                self.__notify_user(data)
            case _:
                logging.error("Unknown action: {}".format(data.get("action")))

    def __notify_user(self, data):
        data["action"] = GuiActions.translate(data.get("action"))
        self.gui.notify(data)

    def __connection(self):
        keep_alive = threading.Thread(target=self.__keep_alive)
        self.active_threads.append(keep_alive)
        keep_alive.start()

        receiver = threading.Thread(target=self.__receiver)
        self.active_threads.append(receiver)
        receiver.start()

    def change_username(self, username):
        self.__user_info['name'] = username
        self.send(action=ClientActions.USER_UPDATE, name=username)

    def change_status(self, status):
        self.__user_info['status'] = status
        self.send(action=ClientActions.USER_UPDATE, status=status)

    @property
    def username(self):
        with self.__user_info_lock:
            return self.__user_info.get("name")

    @property
    def status(self):
        with self.__user_info_lock:
            return self.__user_info.get("status")

    def ask_for_connection(self, user_id):
        self.send(action=ClientActions.ASK_FOR_CONNECTION, user_id=user_id)

    def connect_to_gui(self, gui):
        self.gui = gui

    def accept_connection(self, user_id):
        self.send(action=ClientActions.ACCEPT_CONNECTION, user_id=user_id)

    def reject_connection(self, user_id):
        self.send(action=ClientActions.REJECT_CONNECTION, user_id=user_id)

    def change_encryption(self, encryption):
        self.send(action=ClientActions.CHANGED_ENCRYPTION, encryption=encryption)
        self.aes_socket.change_sending_encryption(encryption)
