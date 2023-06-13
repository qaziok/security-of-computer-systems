import logging
import socket
import threading

from projekt.server.connections.client_manager import ClientManager


class ServerController:
    """Class responsible for managing server connections with clients"""

    def __init__(self, host, port, keys):
        self.accept_thread = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.server_keys = keys
        self.__active_connections_lock = threading.Lock()
        self.active_connections = {}
        self.__threads_lock = threading.Lock()
        self.threads_list = []

    def __enter__(self):
        logging.info('Server started on %s', self.socket.getsockname())
        self.socket.listen()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.accept_thread.join()
        with self.__active_connections_lock:
            for client in self.active_connections.values():
                client.stop_connection()
        with self.__threads_lock:
            for thread in self.threads_list:
                thread.join()

    def run(self):
        """Starts server and waits for user input"""
        self.accept_thread = threading.Thread(target=self.__accept)
        self.accept_thread.start()
        try:
            while input() != 'exit':
                pass
        except KeyboardInterrupt:
            logging.info("Server stopped by user")
        finally:
            self.socket.close()

    def __accept(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                with self.__threads_lock:
                    self.threads_list.append(
                        threading.Thread(target=self.__client_connection,
                                         args=(conn, addr)))
                    self.threads_list[-1].start()
            except OSError:
                logging.info("Listening socket closed")
                break

    def notify_users(self):
        """Notifies all users about update in users list"""
        for _, client in self.active_connections.items():
            client.send_active_users()

    def __client_connection(self, conn, addr):
        with ClientManager(conn, addr, self.server_keys, server_controller=self) as client:
            with self.__active_connections_lock:
                self.active_connections.update({hash(addr): client})

            try:
                client.connection()
            except (ConnectionAbortedError, ConnectionResetError):
                logging.info("Connection with %s aborted", addr)

            finally:
                with self.__active_connections_lock:
                    del self.active_connections[hash(addr)]

    def get_users(self, exclude_id):
        """Returns dict of active users with their status"""
        with self.__active_connections_lock:
            return {client_id: client.active_status() for
                    client_id, client in self.active_connections.items() if
                    client_id != exclude_id}

    def get_user(self, client_id):
        """Returns user with given id or None if user is not connected"""
        with self.__active_connections_lock:
            return self.active_connections.get(client_id)
