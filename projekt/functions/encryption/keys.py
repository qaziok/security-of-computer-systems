from Crypto.PublicKey import RSA


class Keys:
    def __init__(self, *, private_key, public_key):
        self.private_key = private_key
        self.public_key = public_key

    @classmethod
    def generate_keys(cls):
        private_key = RSA.generate(2048)
        public_key = private_key.public_key()

        return cls(private_key=private_key, public_key=public_key)

    @classmethod
    def import_keys(cls, *, private_key=None, public_key=None):
        if private_key is not None:
            private_key = RSA.import_key(private_key)
        if public_key is not None:
            public_key = RSA.import_key(public_key)
        return cls(private_key=private_key, public_key=public_key)


def generate_keys():
    private_key = RSA.generate(2048)
    public_key = private_key.public_key()

    return private_key, public_key
