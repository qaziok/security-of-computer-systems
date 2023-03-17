from Crypto.PublicKey import RSA


def generate_keys():
    private_key = RSA.generate(2048)
    public_key = private_key.public_key()

    return private_key, public_key
