from Crypto.Cipher import PKCS1_OAEP


class RSATranslator:
    def __init__(self, your_private_key, their_public_key):
        self.your_private_key = your_private_key
        self.decrypt_cipher = PKCS1_OAEP.new(self.your_private_key)

        self.their_public_key = their_public_key
        self.encrypt_cipher = PKCS1_OAEP.new(self.their_public_key)

    def encrypt(self, data):
        return self.encrypt_cipher.encrypt(data)

    def decrypt(self, data):
        return self.decrypt_cipher.decrypt(data)
