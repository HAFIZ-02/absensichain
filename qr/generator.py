import qrcode, base64, json
from io import BytesIO
from datetime import datetime
from blockchain.crypto_utils import generate_hmac
from cryptography.fernet import Fernet
from config import Config

def get_fernet():
    key = Config.SECRET_KEY.encode()[:32].ljust(32, b'A')
    return Fernet(base64.urlsafe_b64encode(key))

def generate_student_qr(student_id: int, nis: str, nama: str) -> tuple[str, str]:
    payload = {
        "student_id": student_id, "nis": nis, "nama": nama,
        "timestamp_generated": datetime.now().isoformat()
    }
    # Tandatangani payload
    sig = generate_hmac(payload)
    full_payload = {**payload, "hmac_signature": sig}
    
    # Enkripsi ke bentuk token untuk ditanam di QR
    enc_payload = get_fernet().encrypt(json.dumps(full_payload).encode()).decode()
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(enc_payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    
    return enc_payload, img_b64
