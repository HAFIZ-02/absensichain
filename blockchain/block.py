import json, hashlib
from datetime import datetime, timezone
from blockchain.crypto_utils import sign_data

class Block:
    def __init__(self, index: int, data: dict, previous_hash: str, nonce: int = 0, timestamp: str = None):
        self.index = index
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.merkle_root = self.calc_merkle()
        self.hash = self.calc_hash()
        self.validator_sig = sign_data(self.hash)

    def calc_merkle(self) -> str:
        """Kalkulasi merkle root (simplified untuk struktur 1 log per blok)."""
        return hashlib.sha256(json.dumps(self.data, sort_keys=True).encode()).hexdigest()

    def calc_hash(self) -> str:
        """Kalkulasi hash SHA-256 utama dari head blok."""
        blk = {
            "index": self.index, "timestamp": self.timestamp, "data": self.data, 
            "previous_hash": self.previous_hash, "nonce": self.nonce, "merkle_root": self.merkle_root
        }
        return hashlib.sha256(json.dumps(blk, sort_keys=True).encode()).hexdigest()

    @staticmethod
    def calculate_hash(index: int, timestamp, data: dict, previous_hash: str, nonce: int) -> str:
        """
        Kalkulasi ulang hash blok dari komponen-komponen dasarnya.
        Digunakan untuk memvalidasi integritas data blok yang ada di database.
        """
        from datetime import datetime, date
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                iso_str = obj.isoformat()
                if "+00:00" not in iso_str and not iso_str.endswith("Z"):
                    iso_str += "+00:00"
                return iso_str
            raise TypeError(f"Type {type(obj)} is not JSON serializable")
            
        merkle_root = hashlib.sha256(json.dumps(data, sort_keys=True, default=json_serial).encode()).hexdigest()
        blk = {
            "index": index, "timestamp": timestamp, "data": data,
            "previous_hash": previous_hash, "nonce": nonce, "merkle_root": merkle_root
        }
        return hashlib.sha256(json.dumps(blk, sort_keys=True, default=json_serial).encode()).hexdigest()
