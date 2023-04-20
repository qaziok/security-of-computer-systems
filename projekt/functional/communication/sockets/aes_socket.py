import pickle
import queue

from projekt.functional.communication import Serializer
from projekt.functional.encryption import AESTranslator


class AESSocket(Serializer):
    def __init__(self, socket, key):
        self.socket = socket
        self.aes_translator = AESTranslator(key)
        self.buffer = b''
        self.to_analyze = queue.Queue()

    def send(self, data):
        package = self.aes_translator.encrypt(self._serialize(data))
        self.socket.sendall(self._serialize(package))

    def recv(self):
        package = self._deserialize(self.socket.recv(1024))
        if package is None:
            return None
        return self._deserialize(self.aes_translator.decrypt(*package))

    # def recv(self):
    #     data = self.socket.recv(1024)
    #     parts = data.split(b'\x80\x04')
    #
    #     self.buffer += parts[0]
    #     parts = parts[1:]
    #
    #     if output := self.__value(self.buffer):
    #         self.buffer = b''
    #         yield output
    #
    #     for part in parts:
    #         try:
    #             if output := self.__value(b'\x80\x04' + part):
    #                 yield output
    #             else:
    #                 self.buffer += b'\x80\x04' + part
    #         except:
    #             self.buffer += b'\x80\x04' + part
    #
    #     # package = self._deserialize()
    #     # if package is None:
    #     #     return None
    #     # return self._deserialize(self.aes_translator.decrypt(*package))
    #
    # def __value(self, value):
    #     try:
    #         package = self._deserialize(value)
    #         if package is None:
    #             return None
    #         return self._deserialize(self.aes_translator.decrypt(*package))
    #     except pickle.UnpicklingError:
    #         return None