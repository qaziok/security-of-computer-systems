from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESTranslator(object):
    def __init__(self, session_key):
        self.session_key = session_key

    def encrypt(self, data, *, mode=AES.MODE_EAX):
        aes = AES.new(self.session_key, mode)
        match mode:
            case AES.MODE_EAX:
                return aes.nonce, *aes.encrypt_and_digest(pad(data, AES.block_size))
            case AES.MODE_ECB:
                return aes.encrypt(pad(data, AES.block_size)),
            case AES.MODE_CBC:
                return aes.iv, aes.encrypt(pad(data, AES.block_size))

    def decrypt(self, *args, mode=AES.MODE_EAX):
        match mode:
            case AES.MODE_EAX:
                aes = AES.new(self.session_key, mode, args[0])
                return unpad(aes.decrypt_and_verify(args[1], args[2]), AES.block_size)
            case AES.MODE_ECB:
                aes = AES.new(self.session_key, mode)
                return unpad(aes.decrypt(args[0]), AES.block_size)
            case AES.MODE_CBC:
                aes = AES.new(self.session_key, mode, args[0])
                return unpad(aes.decrypt(args[1]), AES.block_size)
