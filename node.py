import json, asyncio
import websockets
from config import SEED_NODES

class Node:
    def __init__(self, my_url):
        self.my_url = my_url
        self.peers = set()
        self.sockets = {}
        self.on_message = None

    async def connect_to(self, peer_url):
        if peer_url == self.my_url or peer_url in self.peers:
            return
        try:
            ws = await websockets.connect(peer_url)
            self.peers.add(peer_url)
            self.sockets[peer_url] = ws
            print(f"🔗 اتصلنا بـ {peer_url}")
            asyncio.create_task(self._listen(peer_url, ws))
            await ws.send(json.dumps({"type": "hello", "from": self.my_url}))
        except Exception as e:
            print(f"❌ فشل الاتصال بـ {peer_url}: {e}")

    async def _listen(self, peer_url, ws):
        try:
            async for msg in ws:
                data = json.loads(msg)
                if self.on_message:
                    await self.on_message(data, peer_url)
        except Exception:
            pass
        finally:
            self.peers.discard(peer_url)
            self.sockets.pop(peer_url, None)

    async def broadcast(self, message):
        dead = []
        for peer, ws in list(self.sockets.items()):
            try:
                await ws.send(json.dumps(message))
            except Exception:
                dead.append(peer)
        for p in dead:
            self.peers.discard(p)
            self.sockets.pop(p, None)

    async def connect_seeds(self):
        for seed in SEED_NODES:
            await self.connect_to(seed)
