from projekt.functional.communication import Serializer
from projekt.functional.encryption import AESTranslator


class AESSocket(Serializer):
    def __init__(self, socket, key):
        self.socket = socket
        self.aes_translator = AESTranslator(key)

    def send(self, data):
        package = self.aes_translator.encrypt(self._serialize(data))
        self.socket.sendall(self._serialize(package))

    def recv(self):
        package = self._deserialize(self.socket.recv(1024))
        return self._deserialize(self.aes_translator.decrypt(*package))
