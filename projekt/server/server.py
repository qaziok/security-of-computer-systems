import logging
import socket

from projekt.functions.encryption.keys import Keys
from projekt.server.connection.server_controller import ServerController

HOST = socket.gethostname()
IP = socket.gethostbyname(HOST)
PORT = 5000

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

KEYS = Keys.generate_keys()


if __name__ == '__main__':
    with ServerController(IP, PORT, KEYS) as server_controller:
        server_controller.run()
