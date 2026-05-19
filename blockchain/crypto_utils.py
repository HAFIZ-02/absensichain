import hashlib, hmac, json, base64
from config import Config
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

# Generasi key sementara untuk server validator (dalam produksi gunakan key tetap di env)
_private_key = ec.generate_private_key(ec.SECP256K1())

def generate_hmac(payload: dict) -> str:
    """Buat tanda tangan HMAC-SHA256 untuk payload QR Code."""
    msg = json.dumps(payload, sort_keys=True).encode()
    return hmac.new(Config.HMAC_SECRET.encode(), msg, hashlib.sha256).hexdigest()

def verify_hmac(payload: dict, signature: str) -> bool:
    """Validasi tanda tangan HMAC-SHA256."""
    return hmac.compare_digest(generate_hmac(payload), signature)

def sign_data(data: str) -> str:
    """Tanda tangani string (hash blok) menggunakan kurva eliptik ECDSA."""
    sig = _private_key.sign(data.encode(), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode('utf-8')
