import os.path
import socket
import threading

from projekt.app.connections.user_manager import UserManager
from projekt.app.gui.gui_actions import GuiActions
from projekt.functional.communication import UserActions

IP = socket.gethostbyname(socket.gethostname())


class UsersController:
    def __init__(self):
        self.socket = None
        self.id = None
        self.gui = None
        self.accept_thread = None
        self.user_keys = None
        self.active_connections_lock = threading.Lock()
        self.active_connections = {}
        self.known_users = {}
        self.downloadable_files = {}
        self.encryption = 'EAX'

    def start(self, keys):
        self.user_keys = keys
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((IP, 0))
        self.socket.listen()
        self.accept_thread = threading.Thread(target=self.__accept)
        self.accept_thread.start()

    def stop(self):
        with self.active_connections_lock:
            for user in self.active_connections.values():
                user.close()
        if self.socket:
            self.socket.close()
        if self.accept_thread:
            self.accept_thread.join()

    def connect_to_gui(self, gui):
        self.gui = gui

    def add_user(self, data):
        self.known_users.update({data.get('user_id'): data})
        if data.get('connection_address'):
            self.__start_connection_thread(data=data)

    def connection_address(self):
        return self.socket.getsockname()

    def __accept(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                self.__start_connection_thread(conn=conn, addr=addr)
            except OSError:
                break

    def __start_connection_thread(self, **kwargs):
        threading.Thread(target=self.__client_connection, kwargs=kwargs).start()

    def __client_connection(self, **kwargs):
        with UserManager(self.user_keys, users_controller=self) as user:
            user_id, addr = user.create_connection(**kwargs)

            with self.active_connections_lock:
                self.active_connections.update({user_id: user})

            try:
                self.gui.notify({'action': GuiActions.USER_CONNECTED, 'user_id': user_id})
                user.connection()
            finally:
                self.gui.notify({'action': GuiActions.USER_DISCONNECTED, 'user_id': user_id})
                with self.active_connections_lock:
                    del self.active_connections[user_id]

    def disconnect(self, user_id):
        with self.active_connections_lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].close()

    def find_user(self, code):
        for user in self.known_users.values():
            if user.get('find_code') == code:
                return user
        return None

    def send(self, user_id, message, file):
        data = {}

        if file:
            file_id = hash(file)
            self.downloadable_files.update({file_id: file})
            data.update(file=(file_id, os.path.basename(file)))

        if message:
            data.update(message=message)

        with self.active_connections_lock:
            self.active_connections[user_id].send(action=UserActions.MESSAGE, **data)

    def download_file(self, user_id, file_id):
        channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        channel.bind((IP, 0))
        channel.listen(1)

        with self.active_connections_lock:
            self.active_connections[user_id].download_file(channel, file_id)

    def change_encryption(self, encryption):
        self.encryption = encryption
        with self.active_connections_lock:
            for user in self.active_connections.values():
                user.change_encryption(encryption)
