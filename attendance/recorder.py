from sqlalchemy.orm import Session as DBSession
from datetime import datetime
from database.models import Attendance, Session
from blockchain.chain import Blockchain
from blockchain.smart_contract import AttendanceContract
from blockchain.crypto_utils import verify_hmac
from qr.validator import decrypt_qr
from attendance.status_calculator import determine_status


def record_attendance(db: DBSession, qr_data: str, session_id: int) -> tuple[bool, str]:
    """Catat kehadiran siswa via QR ke blockchain dan database.

    Urutan:
      1. Dekripsi QR → dapatkan payload asli
      2. Verifikasi HMAC pada payload asli (tanpa session_id)
      3. Jalankan Smart Contract (CONTRACT-02 s/d CONTRACT-06)
      4. Tentukan status (hadir/terlambat)
      5. Tambahkan blok baru ke blockchain
      6. Simpan attendance ke database relasional
    """
    payload = decrypt_qr(qr_data)
    if not payload:
        return False, "Data QR Code rusak atau tidak valid."

    # ── PENTING: ambil HMAC SEBELUM menambahkan session_id ──────────────
    # HMAC digenerate dari payload asli (tanpa session_id & hmac_signature)
    qr_sig = payload.pop('hmac_signature', '')

    # Verifikasi HMAC pada payload ASLI (belum ada session_id)
    if not verify_hmac(payload, qr_sig):
        return False, "CONTRACT-01: QR signature tidak valid. QR mungkin telah dimanipulasi."

    # Setelah HMAC terverifikasi, baru tambahkan session_id untuk kontrak lainnya
    payload['session_id'] = session_id

    bc = Blockchain()
    latest_hash = bc.get_latest().hash

    # Jalankan CONTRACT-02 s/d CONTRACT-06 (CONTRACT-01 sudah diverifikasi di atas)
    valid, msg = AttendanceContract.validate(db, payload, latest_hash)
    if not valid:
        return False, msg

    sess = db.query(Session).filter(Session.id == session_id).first()
    now = datetime.now()
    status = determine_status(sess, now)

    # Tambahkan blok baru ke blockchain
    block_data = {
        "student_id": payload["student_id"],
        "session_id": session_id,
        "status": status,
        "scan_time": now.isoformat(),
    }
    new_block = bc.add_block(block_data)

    # Simpan ke tabel attendances (relasional)
    att = Attendance(
        student_id=payload["student_id"],
        session_id=session_id,
        status=status,
        scan_time=now,
        block_index=new_block.index,
    )
    db.add(att)
    db.commit()

    nama = payload.get("nama", "Siswa")
    return True, f"{nama} berhasil dicatat! Status: **{status.upper()}** (Block #{new_block.index})"
