import json, os
from block import Block
from transaction import Transaction
from config import DIFFICULTY, MINING_REWARD

class Blockchain:
    def __init__(self, file="chain.json"):
        self.file = file
        self.chain = []
        self.pending = []
        if os.path.exists(self.file):
            self.load()
        if not self.chain:
            self.create_genesis()

    def create_genesis(self):
        genesis = Block(0, [], "0"*64, difficulty=DIFFICULTY)
        genesis.mine()
        self.chain.append(genesis)
        self.save()

    def save(self):
        with open(self.file, "w") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)

    def load(self):
        with open(self.file) as f:
            data = json.load(f)
        self.chain = [Block.from_dict(b) for b in data]

    def available_balance(self, address):
        bal = self.balance(address)
        for tx in self.pending:
            if tx.sender == address:
                bal -= tx.amount
        return bal

    def add_transaction(self, tx):
        if not tx.verify():
            raise ValueError("توقيع المعاملة غير صحيح")
        if tx.amount <= 0:
            raise ValueError("المبلغ لازم أكبر من صفر")
        if tx.sender != "SYSTEM" and self.available_balance(tx.sender) < tx.amount:
            raise ValueError("الرصيد غير كافي")
        self.pending.append(tx)

    def balance(self, address):
        bal = 0.0
        for blk in self.chain:
            for tx in blk.transactions:
                if tx.sender == address:
                    bal -= tx.amount
                if tx.recipient == address:
                    bal += tx.amount
        return bal

    def mine_pending(self, miner_address):
        reward = Transaction("SYSTEM", miner_address, MINING_REWARD)
        block_txs = self.pending + [reward]
        prev = self.chain[-1]
        new_block = Block(len(self.chain), block_txs, prev.hash, difficulty=DIFFICULTY)
        new_block.mine()
        self.chain.append(new_block)
        self.pending = []
        self.save()
        return new_block

    def is_valid_chain(self, chain):
        for i in range(1, len(chain)):
            cur, prev = chain[i], chain[i-1]
            if cur.hash != cur.compute_hash():
                return False, f"Block {i} hash mismatch"
            if cur.previous_hash != prev.hash:
                return False, f"Block {i} not linked"
            if not cur.hash.startswith("0"*cur.difficulty):
                return False, f"Block {i} not mined"
        return True, "OK"

    def is_valid(self):
        return self.is_valid_chain(self.chain)

    def replace_chain(self, new_chain):
        if len(new_chain) <= len(self.chain):
            return False, "السلسلة الجديدة مش أطول"
        ok, msg = self.is_valid_chain(new_chain)
        if not ok:
            return False, f"السلسلة الجديدة غلط: {msg}"
        self.chain = new_chain
        self.save()
        return True, "تم استبدال السلسلة"
