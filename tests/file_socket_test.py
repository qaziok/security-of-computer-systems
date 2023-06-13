import os
import socket
import threading
import time

from projekt.functional.communication.sockets import FileSocket

SESSION_KEY = b'12345678901234567890123456789012'

FILES_DIR = 'D:\\semestr_6\\bsk\\security-of-computer-systems\\projekt\\app\\downloads'

DATA = {}


def _sender(conn, fa, e):
    global DATA

    fn = os.path.basename(fa)
    print(f"Sending file: {fn} with {e} encryption")
    start = time.time_ns()

    with open(fa, 'rb') as file:
        fs = FileSocket(conn, SESSION_KEY).change_sending_encryption(e)
        fs.send(file.read())

    timer = (time.time_ns() - start) / 1e9
    print(f"File sent in {timer}")

    DATA[fn][e]['sender'] = timer


def _receiver(sock, fn, e):
    global DATA

    print(f"Downloading file: {fn} with {e} encryption")
    start = time.time_ns()

    conn, addr = sock.accept()

    fs = FileSocket(conn, SESSION_KEY).change_receiving_encryption(e)
    fs.recv(lambda p: print(f"Progress: {p}%"))

    timer = (time.time_ns() - start) / 1e9
    print(f"File downloaded in {timer}")

    DATA[fn][e]['receiver'] = timer


if __name__ == '__main__':
    for file_name in os.listdir(FILES_DIR):
        DATA[file_name] = {}
        file_addr = os.path.join(FILES_DIR, file_name)

        for encryption in ['EAX', 'ECB', 'CBC']:
            DATA[file_name][encryption] = {}
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('localhost', 5000))
            server.listen()

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(server.getsockname())

            receiver = threading.Thread(target=_receiver, args=(server, file_name, encryption))
            receiver.start()

            sender = threading.Thread(target=_sender, args=(client, file_addr, encryption))
            sender.start()

            sender.join()
            receiver.join()

            server.close()
            client.close()

    # save DATA to json file
    import json

    with open('data.json', 'w') as f:
        json.dump(DATA, f, indent=4)
