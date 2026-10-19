import os

CHAIN_NAME = "MG Chain"
CHAIN_ID = 7737005
DIFFICULTY = 3
MINING_REWARD = 10.0

PORT = int(os.environ.get("PORT", 8000))

SEED_NODES = os.environ.get("SEED_NODES", "").split(",")
SEED_NODES = [s.strip() for s in SEED_NODES if s.strip()]

SYNC_INTERVAL = 10

CHAIN_FILE = f"chain_{PORT}.json"
