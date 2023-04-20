import os.path
import socket
import threading

from projekt.app.connections.user_manager import UserManager
from projekt.app.gui.gui_actions import GuiActions
from projekt.functional.communication import UserActions

IP = socket.gethostbyname(socket.gethostname())


class UsersController:
    def __init__(self, keys):
        self.socket = None
        self.id = None
        self.gui = None
        self.accept_thread = None
        self.user_keys = keys
        self.active_connections_lock = threading.Lock()
        self.active_connections = {}
        self.known_users = {}
        self.downloadable_files = {}

    def start(self, username, password):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((IP, 0))
        self.socket.listen()
        self.accept_thread = threading.Thread(target=self.__accept)
        self.accept_thread.start()

    def stop(self):
        for user in self.active_connections.values():
            user.close()
        self.socket.close()
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
                with self.active_connections_lock:
                    del self.active_connections[user_id]

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
        with self.active_connections_lock:
            self.active_connections[user_id].send(action=UserActions.DOWNLOAD_FILE, file_id=file_id)
