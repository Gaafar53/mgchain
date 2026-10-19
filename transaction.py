import json, time, hashlib
import ecdsa

class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None, signature=None, public_key=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = float(amount)
        self.timestamp = int(timestamp) if timestamp is not None else int(time.time())
        self.signature = signature
        self.public_key = public_key

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "public_key": self.public_key,
        }

    def payload(self):
        return json.dumps({
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": str(self.amount),
            "timestamp": self.timestamp,
        }, sort_keys=True).encode()

    def hash(self):
        return hashlib.sha256(self.payload()).hexdigest()

    def sign(self, private_key_hex):
        sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
        self.signature = sk.sign(self.payload()).hex()
        self.public_key = sk.get_verifying_key().to_string().hex()
        return self

    def verify(self):
        if self.sender == "SYSTEM":
            return True
        if not self.signature or not self.public_key:
            return False
        try:
            vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(self.public_key), curve=ecdsa.SECP256k1)
            return vk.verify(bytes.fromhex(self.signature), self.payload())
        except Exception:
            return False
