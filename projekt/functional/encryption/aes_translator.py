from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class AESTranslator(object):
    def __init__(self, session_key):
        self.session_key = session_key

    def encrypt(self, data, *, mode=AES.MODE_EAX):
        aes = AES.new(self.session_key, mode)
        excepted_data, tag = aes.encrypt_and_digest(pad(data, AES.block_size))
        return aes.nonce, excepted_data, tag

    def decrypt(self, nonce, data, tag, *, mode=AES.MODE_EAX):
        aes = AES.new(self.session_key, mode, nonce)
        return aes.decrypt_and_verify(data, tag)
