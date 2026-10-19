import ecdsa, hashlib

class Wallet:
    def __init__(self, private_key_hex=None):
        if private_key_hex:
            self.private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
        else:
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    def private_hex(self):
        return self.private_key.to_string().hex()

    def public_hex(self):
        return self.public_key.to_string().hex()

    def address(self):
        pub = self.public_hex().encode()
        return "MG" + hashlib.sha256(pub).hexdigest()[:38]
