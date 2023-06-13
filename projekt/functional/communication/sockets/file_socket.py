from projekt.functional.communication.sockets import AESSocket


class FileSocket(AESSocket):
    def __init__(self, socket, key):
        super().__init__(socket, key)

    def send(self, data: bytes):
        package = self.aes_translator.encrypt(data, mode=self.sending_encryption)
        to_send = self._serialize(package)
        self.socket.send(str(len(to_send)).encode())
        self.socket.sendall(to_send)

    def recv(self, gui_notify_func=(lambda p: None)):
        package_size = int(self.socket.recv(1024).decode())
        buffer = b''
        progress = 0
        while len(buffer) < package_size:
            data = self.socket.recv(4096)
            if not data:
                break
            buffer += data

            if (np := round(len(buffer)*100 / package_size)) > progress:
                gui_notify_func((progress := np))

        if len(buffer) != package_size:
            raise ValueError('Incorrect package size')

        package = self._deserialize(buffer)
        return self.aes_translator.decrypt(*package, mode=self.receiving_encryption)
