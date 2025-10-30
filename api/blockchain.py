from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import hashlib, json, os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase setup ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# --- Blockchain classes ---
class Block:
    def __init__(self, index, timestamp, data, previous_hash=""):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        raw = f"{self.index}{self.previous_hash}{self.timestamp}{json.dumps(self.data, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, datetime.now().isoformat(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)


@app.get("/products")
def get_products():
    MICchain = Blockchain()
    res = supabase.table("MarketPlace").select(
        "id, created_at, name, price, original_price, image, brand, category"
    ).execute()

    if res.error:
        return {"error": str(res.error)}

    for r in res.data:
        data = {
            "id": r["id"],
            "name": r["name"],
            "price": r["price"],
            "originalPrice": r["original_price"],
            "image": r["image"],
            "brand": r["brand"],
            "category": r["category"],
        }
        MICchain.add_block(Block(r["id"], r["created_at"], data))

    return {"products": [b.data for b in MICchain.chain if isinstance(b.data, dict)]}
