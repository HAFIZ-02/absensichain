from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from database.models import Student, Session, Attendance


class AttendanceContract:
    """Smart Contract validasi absensi blockchain AbsenChain."""

    @staticmethod
    def validate(
        db: DBSession,
        payload: dict,
        latest_hash: str,
    ) -> tuple[bool, str]:
        """Eksekusi aturan validasi CONTRACT-02 s/d CONTRACT-05.

        CONTRACT-01 (HMAC) diverifikasi di recorder.py sebelum method ini dipanggil.

        Args:
            db: SQLAlchemy DB session
            payload: dict yang sudah berisi student_id, session_id (tanpa hmac_signature)
            latest_hash: hash blok terakhir (untuk CONTRACT-06 internal chain check)

        Returns:
            (True, "Valid") jika semua kontrak lolos
            (False, "CONTRACT-XX: ...") jika gagal
        """
        student_id = payload.get("student_id")
        session_id = payload.get("session_id")

        # CONTRACT-02: student_id tidak terdaftar / akun tidak aktif
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return False, "CONTRACT-02: Akun siswa tidak ditemukan dalam sistem."
        if student.user.status.lower() != 'active':
            return False, "CONTRACT-02: Akun siswa belum aktif atau telah dinonaktifkan."

        # CONTRACT-03: session_id tidak merujuk sesi aktif
        sess = db.query(Session).filter(Session.id == session_id).first()
        if not sess:
            return False, "CONTRACT-03: Sesi tidak ditemukan."
        if sess.status != 'open':
            return False, "CONTRACT-03: Sesi absensi sudah ditutup."

        # CONTRACT-04: siswa sudah punya record di sesi ini
        existing = db.query(Attendance).filter_by(
            student_id=student.id, session_id=sess.id
        ).first()
        if existing and existing.status in ['hadir', 'terlambat']:
            return False, f"CONTRACT-04: {student.nama_lengkap} sudah tercatat hadir pada sesi ini."

        # CONTRACT-05: waktu scan di luar rentang jam sesi
        now_time = datetime.now().time()
        
        # Pastikan format jam ditangani dengan aman baik string "08:30:00" maupun objek time
        from datetime import time as dt_time
        def get_time(t) -> dt_time:
            if isinstance(t, dt_time): return t
            parts = str(t).split(":")
            return dt_time(int(parts[0]), int(parts[1]))

        jam_mulai_time = get_time(sess.jam_mulai)
        jam_selesai_time = get_time(sess.jam_selesai)

        if now_time < jam_mulai_time or now_time > jam_selesai_time:
            return (
                False,
                f"CONTRACT-05: Waktu scan di luar rentang sesi "
                f"({jam_mulai_time.strftime('%H:%M')}–{jam_selesai_time.strftime('%H:%M')}).",
            )

        return True, "Valid"
