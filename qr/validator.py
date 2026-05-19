import json
from qr.generator import get_fernet

def decrypt_qr(encrypted_data: str) -> dict:
    try:
        decrypted = get_fernet().decrypt(encrypted_data.encode()).decode()
        return json.loads(decrypted)
    except Exception:
        return None
