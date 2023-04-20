import logging
import socket
import threading

from projekt.server.connections.client_manager import ClientManager


class ServerController:
    def __init__(self, host, port, keys):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.server_keys = keys
        self.active_connections_lock = threading.Lock()
        self.active_connections = {}

    def __enter__(self):
        logging.info(f"Server started on {self.socket.getsockname()}")
        self.socket.listen()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()

    def run(self):
        accept_thread = threading.Thread(target=self.__accept)
        accept_thread.start()
        while input() != 'exit':
            pass

    def __accept(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                threading.Thread(target=self.__client_connection, args=(conn, addr)).start()
            except OSError:
                break

    def notify_users(self):
        logging.info("Notifying users about update in users list")
        for client_id, client in self.active_connections.items():
            client.send_active_users()

    def __client_connection(self, conn, addr):
        with ClientManager(conn, addr, self.server_keys, server_controller=self) as client:
            with self.active_connections_lock:
                self.active_connections.update({hash(addr): client})

            try:
                client.connection()

            finally:
                with self.active_connections_lock:
                    del self.active_connections[hash(addr)]

    def get_users(self, exclude_id):
        with self.active_connections_lock:
            return {client_id: client.active_status() for client_id, client in self.active_connections.items() if
                    client_id != exclude_id}

    def get_user(self, client_id):
        with self.active_connections_lock:
            return self.active_connections.get(client_id)
