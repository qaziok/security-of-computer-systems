import pickle
import socket
import threading

from time import sleep
from Crypto.PublicKey import RSA

from projekt.functions.encryption import generate_keys, RSATranslator

HOST = socket.gethostname()
IP = socket.gethostbyname(HOST)
PORT = 3002

SERVER_IP = IP
SERVER_PORT = 5000

PRIVATE_KEY, PUBLIC_KEY = generate_keys()


def server_handshake(conn):
    conn.sendall(PUBLIC_KEY.exportKey())

    server_public_key = RSA.importKey(conn.recv(1024))

    rsa_translator = RSATranslator(PRIVATE_KEY, server_public_key)

    data = {
        "name": "test",
        "status": "test"
    }

    conn.sendall(rsa_translator.encrypt(pickle.dumps(data)))


def server_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((SERVER_IP, SERVER_PORT))
    except ConnectionRefusedError:
        print("Connection refused")
        return

    server_handshake(s)

    while True:
        try:
            s.sendall("works!".encode())
            sleep(10)
        except ConnectionAbortedError:
            print("Connection lost")
            break


if __name__ == '__main__':
    threading.Thread(target=server_connection).start()
    while True:
        sleep(1)
