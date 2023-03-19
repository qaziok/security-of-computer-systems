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
        while True:
            self.__accept()

    def __accept(self):
        conn, addr = self.socket.accept()
        threading.Thread(target=self.__client_connection, args=(conn, addr)).start()

    def __client_connection(self, conn, addr):
        with ClientManager(conn, addr, self.server_keys, server_controller=self) as client:
            with self.active_connections_lock:
                self.active_connections.update({hash(addr): client})
            client.connection()
            with self.active_connections_lock:
                del self.active_connections[hash(addr)]
