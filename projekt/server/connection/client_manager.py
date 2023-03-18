import socket

import select
import logging

from projekt.functions.communication import Serializer
from projekt.functions.encryption import RSATranslator
from projekt.functions.encryption.keys import Keys

# TODO: Pass this as a parameter
CLIENT_TIMER = 5


class ClientManager(Serializer):
    def __init__(self, conn, addr, keys, *, server_controller):
        self.conn = conn
        self.addr = addr
        self.server_keys = keys
        self.server_controller = server_controller

        self.user_info = None
        self.user_keys = None
        self.rsa_translator = None

    def __enter__(self):
        logging.info(f"Connected to {self.addr}")
        self.__handshake()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info(f"Disconnected from {self.addr}")
        self.conn.close()

    def __handshake(self):
        self.user_keys = Keys.import_keys(public_key=self.conn.recv(1024))
        self.conn.sendall(self.server_keys.public_key.exportKey())

        logging.info(f"Keys successfully exchanged with {self.addr}")

        self.rsa_translator = RSATranslator(self.server_keys.private_key, self.user_keys.public_key)
        self.user_info = self.recv()

    def send(self, data):
        self.conn.sendall(self.rsa_translator.encrypt(self._serialize(data)))

    def recv(self):
        try:
            return self._deserialize(self.rsa_translator.decrypt(self.conn.recv(1024)))
        except ValueError:
            logging.error(f"Received invalid data from {self.addr}")
            return None

    def connection(self):
        while True:
            ready = select.select([self.conn], [], [], CLIENT_TIMER)
            if not ready[0]:
                break

            data = self.recv()

            if data is None:
                break

            logging.info(f"Received data from {self.addr}")
            self.handle(data)

    def handle(self, data):
        pass