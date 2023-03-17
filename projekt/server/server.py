import pickle
import socket
import threading
import select

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from projekt.functions.encryption import generate_keys

HOST = socket.gethostname()
IP = socket.gethostbyname(HOST)
PORT = 5000

CLIENT_TIMER = 5

PRIVATE_KEY, PUBLIC_KEY = generate_keys()

clients_lock = threading.Lock()
clients = {}


def client_handshake(cconn, cname, cid, caddr):
    client_public_key = RSA.importKey(cconn.recv(1024))
    cconn.sendall(PUBLIC_KEY.exportKey())

    data = cconn.recv(1024)

    cipher_rsa = PKCS1_OAEP.new(PRIVATE_KEY)
    data = cipher_rsa.decrypt(data)
    data = pickle.loads(data)

    with clients_lock:
        clients[cid] = {
            "name": data.get("name", cname),
            "status": data.get("status", "Available"),
            "addr": caddr,
            "public_key": client_public_key
        }


def client_connection(conn, addr):
    client_name = socket.gethostbyaddr(addr[0])[0]
    client_id = hash(addr)

    client_handshake(conn, client_name, client_id, addr)

    print(f"Connected to {clients[client_id]['name']} ({addr})")

    while True:
        ready = select.select([conn], [], [], CLIENT_TIMER)
        if ready[0]:
            data = conn.recv(1024)
            print(f"Received {data.decode()} from {addr}")
        else:
            conn.close()
            print(f"Connection with {addr} closed")
            with clients_lock:
                del clients[client_id]
            break


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((IP, PORT))
        print(f"Listening on {IP}:{PORT}...")

        s.listen()
        while True:
            print("Waiting for connection...")
            conn, addr = s.accept()
            threading.Thread(target=client_connection, args=(conn, addr)).start()
