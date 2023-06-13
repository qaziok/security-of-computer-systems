import os

from Crypto.PublicKey import RSA

KEY_SIZE = 2048
DEFAULT_PASSPHRASE = 'default'


class Keys:
    def __init__(self, *, private_key, public_key, passphrase):
        self.private_key = private_key
        self.public_key = public_key
        self.passphrase = passphrase or DEFAULT_PASSPHRASE

    @classmethod
    def generate_keys(cls, *, passphrase=None):
        private_key = RSA.generate(KEY_SIZE)
        public_key = private_key.public_key()

        return cls(private_key=private_key, public_key=public_key, passphrase=passphrase)

    @classmethod
    def import_keys(cls, *, private_key=None, public_key=None, passphrase=None):
        if private_key is not None:
            private_key = RSA.import_key(private_key, passphrase=passphrase)
        if public_key is not None:
            public_key = RSA.import_key(public_key)
        return cls(private_key=private_key, public_key=public_key, passphrase=passphrase)

    def from_files(self, public_key_file, private_key_file):
        with open(public_key_file, 'r') as f:
            self.public_key = RSA.import_key(f.read())

        with open(private_key_file, 'r') as f:
            self.private_key = RSA.import_key(f.read(), passphrase=self.passphrase)

        return self

    def save_to_files(self, directory, *, public_key_name='public.pem', private_key_name='private.pem'):
        if not os.path.exists(directory):
            os.makedirs(directory)

        public_key_dir = os.path.join(directory, public_key_name)
        private_key_dir = os.path.join(directory, private_key_name)

        self.__save_to_file_with_backup(public_key_dir, private_key_dir)

    def __save_to_file_with_backup(self, public_key_dir, private_key_dir):
        private_key = self.private_key.exportKey(passphrase=self.passphrase)
        public_key = self.public_key.exportKey()

        with open(public_key_dir, 'wb') as f:
            f.write(public_key)

        with open(private_key_dir, 'wb') as f:
            f.write(private_key)
