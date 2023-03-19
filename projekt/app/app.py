import socket
from time import sleep

from projekt.app.connections import ServerManager
from projekt.functional.encryption import Keys

HOST = socket.gethostname()
IP = socket.gethostbyname(HOST)
PORT = 3002

SERVER_IP = IP
SERVER_PORT = 5000

KEYS = Keys.generate_keys()


def server_connection():
    with ServerManager(SERVER_IP, SERVER_PORT, KEYS) as server_manager:

        while True:
            server_manager.send({"test": "test"})
            sleep(3)
            #server_manager.send("leaving")
            #break


if __name__ == '__main__':
    server_connection()
