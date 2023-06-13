import logging
import select

from Crypto.Random import get_random_bytes

from projekt.functional.communication import ClientActions, ServerActions
from projekt.functional.communication.sockets import RSASocket
from projekt.functional.communication.sockets.aes_socket import AESSocket
from projekt.functional.encryption.keys import Keys

# TODO: Pass this as a parameter
CLIENT_TIMER = 60


class ClientManager:
    """ Class responsible for managing client connection to the server """
    def __init__(self, conn, addr, keys, *, server_controller):
        self.conn = conn
        self.addr = addr
        self.server_keys = keys
        self.server_controller = server_controller

        self.connected = None
        self.user_info = None
        self.user_keys = None
        self.aes_socket = None
        self.rsa_socket = None
        self.session_key = None

    def __enter__(self):
        logging.info("Connected to %s", self.addr)
        self.__handshake()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info("Disconnected from %s", self.addr)
        self.conn.close()
        self.server_controller.notify_users()

    def __handshake(self):
        self.user_keys = Keys.import_keys(public_key=self.conn.recv(1024))
        self.conn.sendall(self.server_keys.public_key.exportKey())

        logging.info("Public keys successfully exchanged with %s", self.addr)

        self.rsa_socket = RSASocket(
            self.conn, self.server_keys.private_key, self.user_keys.public_key
        )

        self.session_key = self.rsa_socket.recv()

        logging.info("Session key successfully exchanged with %s", self.addr)

        self.aes_socket = AESSocket(self.conn, self.session_key)

        self.user_info = self.recv()
        self.connected = True
        logging.info("User %s connected", self.user_info.get('name'))

    def send(self, *, action=None, **data):
        data['action'] = action

        self.aes_socket.send(data)

    def recv(self):
        return self.aes_socket.recv()

    def connection(self):
        self.server_controller.notify_users()

        while self.connected:
            ready = select.select([self.conn], [], [], CLIENT_TIMER)
            if not ready[0]:
                break

            data = self.recv()

            if data is None:
                break

            logging.info("Received %s from %s", data, self.addr)
            self.handle(data)

    # Handle received data
    def handle(self, data):
        match data.get("action"):
            case ClientActions.LEAVE:
                self.connected = False
            case ClientActions.USER_UPDATE:
                self.user_info.update(data)
                self.server_controller.notify_users()
            case ClientActions.ASK_FOR_CONNECTION:
                self.server_controller.get_user(
                    data.get("user_id")
                ).ask_for_connection(hash(self.addr))
            case ClientActions.ACCEPT_CONNECTION:
                self.connection_approved(data.get("user_id"))
            case ClientActions.CHANGED_ENCRYPTION:
                self.aes_socket.change_receiving_encryption(data.get("encryption"))
            case ClientActions.ACTIVE | None:
                pass
            case _:
                print(data)

    # Send active users(except this one) to this user
    def send_active_users(self):
        users_information = self.server_controller.get_users(hash(self.addr))
        self.send(action=ServerActions.ACTIVE_USERS, users=users_information)

    # User status that will be sent to other users
    def active_status(self):
        return {
            "id": hash(self.addr),
            "name": self.user_info.get("name"),
            "status": self.user_info.get("status"),
            "active": self.connected
        }

    # User with user_id wants to connect with this user
    def ask_for_connection(self, user_id):
        self.send(action=ServerActions.ASK_USER_FOR_CONNECTION, user_id=user_id)

    # User with user_id accepted connection with this user
    def connection_approved(self, user_id):
        connecting_user = self.server_controller.get_user(user_id)
        find_code = get_random_bytes(16)

        # Send this user other user id and public key
        self.send(action=ServerActions.CONNECTION_APPROVED, user_id=user_id,
                  public_key=connecting_user.user_keys.public_key.exportKey(),
                  find_code=find_code)

        # Send other user this user id, public key and connection address
        connecting_user.send(action=ServerActions.CONNECTION_APPROVED, user_id=hash(self.addr),
                             public_key=self.user_keys.public_key.exportKey(),
                             connection_address=self.user_info.get("connection_address"),
                             find_code=find_code)

    def stop_connection(self):
        self.connected = False
