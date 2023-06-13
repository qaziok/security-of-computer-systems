import queue
from Crypto.Cipher import AES

from projekt.functional.communication import Serializer
from projekt.functional.encryption import AESTranslator

SUPPORTED_ENCRYPTIONS = {
    "EAX": AES.MODE_EAX,
    "ECB": AES.MODE_ECB,
    "CBC": AES.MODE_CBC
}


class AESSocket(Serializer):
    def __init__(self, socket, key):
        self.socket = socket
        self.aes_translator = AESTranslator(key)
        self.sending_encryption = AES.MODE_EAX
        self.receiving_encryption = AES.MODE_EAX
        self.buffer = b''
        self.to_analyze = queue.Queue()

    def send(self, data):
        package = self.aes_translator.encrypt(self._serialize(data), mode=self.sending_encryption)
        self.socket.sendall(self._serialize(package))

    def recv(self):
        package = self._deserialize(self.socket.recv(1024))
        if package is None:
            return None
        return self._deserialize(self.aes_translator.decrypt(*package, mode=self.receiving_encryption))

    def change_sending_encryption(self, mode):
        self.sending_encryption = self.__translate(mode)
        return self

    def change_receiving_encryption(self, mode):
        self.receiving_encryption = self.__translate(mode)
        return self

    def copy(self, new_socket, key):
        return AESSocket(new_socket, key). \
            change_sending_encryption(self.sending_encryption). \
            change_receiving_encryption(self.receiving_encryption)

    @staticmethod
    def __translate(mode):
        if mode in SUPPORTED_ENCRYPTIONS.values():
            return mode
        return SUPPORTED_ENCRYPTIONS[mode]
