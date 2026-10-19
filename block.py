import json, time, hashlib
from transaction import Transaction

class Block:
    def __init__(self, index, transactions, previous_hash, difficulty=3, nonce=0, timestamp=None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = nonce
        self.timestamp = int(timestamp) if timestamp is not None else int(time.time())
        self.hash = self.compute_hash()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine(self):
        target = "0" * self.difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()
        return self

    @staticmethod
    def from_dict(d):
        txs = [Transaction(**t) for t in d["transactions"]]
        blk = Block(d["index"], txs, d["previous_hash"], d["difficulty"], d["nonce"], d["timestamp"])
        blk.hash = d["hash"]
        return blk
