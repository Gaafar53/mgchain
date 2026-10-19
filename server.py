from flask import Flask, request, jsonify
from flask_sock import Sock
from blockchain import Blockchain
from transaction import Transaction
from block import Block
from node import Node
from config import PORT, CHAIN_FILE
import json, threading, asyncio
import requests as req

app = Flask(__name__)
sock = Sock(app)
bc = Blockchain(CHAIN_FILE)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

node = Node(f"ws://localhost:{PORT}/ws")

def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, loop)

@app.route("/")
def home():
    return jsonify({
        "name": "MG Chain",
        "blocks": len(bc.chain),
        "pending": len(bc.pending),
        "peers": list(node.peers),
    })

@app.route("/chain")
def get_chain():
    return jsonify([b.to_dict() for b in bc.chain])

@app.route("/balance/<address>")
def balance(address):
    return jsonify({"address": address, "balance": bc.balance(address)})

@app.route("/transaction", methods=["POST"])
def new_tx():
    d = request.get_json()
    tx = Transaction(d["sender"], d["recipient"], d["amount"],
                     signature=d.get("signature"), public_key=d.get("public_key"))
    try:
        bc.add_transaction(tx)
        run_async(node.broadcast({"type": "tx", "tx": tx.to_dict()}))
        return jsonify({"status": "added"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/mine", methods=["POST"])
def mine():
    d = request.get_json()
    blk = bc.mine_pending(d["miner_address"])
    run_async(node.broadcast({"type": "block", "block": blk.to_dict()}))
    return jsonify({"status": "mined", "block": blk.to_dict()})

@app.route("/valid")
def valid():
    ok, msg = bc.is_valid()
    return jsonify({"valid": ok, "message": msg})

@app.route("/peers", methods=["POST"])
def add_peer():
    d = request.get_json()
    peer = d["peer"]
    run_async(node.connect_to(peer))
    return jsonify({"status": "connecting", "peer": peer})

@app.route("/sync", methods=["POST"])
def sync():
    d = request.get_json()
    peer = d["peer"]
    try:
        http_url = peer.replace("ws://", "http://").replace("/ws", "")
        r = req.get(f"{http_url}/chain", timeout=5)
        data = r.json()
        new_chain = [Block.from_dict(b) for b in data]
        ok, msg = bc.replace_chain(new_chain)
        return jsonify({"synced": ok, "message": msg, "blocks": len(bc.chain)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@sock.route("/ws")
def ws_handler(ws):
    print("🔌 اتصال WebSocket جديد")
    try:
        while True:
            msg = ws.receive()
            data = json.loads(msg)
            handle_p2p(data, ws)
    except Exception as e:
        print(f"WS disconnected: {e}")

def handle_p2p(data, ws):
    t = data.get("type")
    if t == "hello":
        peer_url = data["from"]
        node.peers.add(peer_url)
        try:
            ws.send(json.dumps({"type": "chain", "chain": [b.to_dict() for b in bc.chain]}))
        except Exception:
            pass
    elif t == "chain":
        new_chain = [Block.from_dict(b) for b in data["chain"]]
        ok, msg = bc.replace_chain(new_chain)
        print(f"📥 chain: {ok} - {msg}")
    elif t == "block":
        blk = Block.from_dict(data["block"])
        if blk.previous_hash == bc.chain[-1].hash:
            ok, msg = bc.is_valid_chain(bc.chain + [blk])
            if ok:
                bc.chain.append(blk)
                bc.save()
                print(f"✅ بلوك جديد #{blk.index}")
    elif t == "tx":
        try:
            tx = Transaction(**data["tx"])
            if tx.verify():
                bc.pending.append(tx)
                print(f"📨 معاملة جديدة: {tx.amount}")
        except Exception:
            pass

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_loop, daemon=True).start()

if __name__ == "__main__":
    print(f"🚀 MG Chain node شغال على بورت {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
