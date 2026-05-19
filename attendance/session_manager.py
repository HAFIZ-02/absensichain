from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from database.models import Session, Attendance, Student, User
from blockchain.chain import Blockchain


def close_session(db: DBSession, session_id: int) -> list[dict]:
    """Tutup sesi absensi.

    Untuk setiap siswa aktif yang belum scan:
      - Catat sebagai ABSEN di tabel attendances
      - Buat blok blockchain baru

    Returns:
        list[dict]: Rekap lengkap seluruh siswa [{nama, nis, kelas, status, scan_time, block_index}]
    """
    sess = db.query(Session).filter(Session.id == session_id).first()
    if not sess:
        return []

    # Tandai sesi sebagai closed
    sess.status = 'closed'
    db.flush()

    bc = Blockchain()

    # Ambil semua siswa aktif (join ke User, filter status)
    students = (
        db.query(Student)
        .join(User, Student.user_id == User.id)
        .filter(User.status.ilike('active'))
        .all()
    )

    # Mapping student_id -> Attendance untuk siswa yang sudah scan
    attended = {
        a.student_id: a
        for a in db.query(Attendance).filter(Attendance.session_id == session_id).all()
    }

    recap = []
    scan_time_now = datetime.now()

    for student in students:
        if student.id in attended:
            att = attended[student.id]
            recap.append({
                "nama": student.nama_lengkap,
                "nis": student.nis,
                "kelas": student.kelas,
                "status": att.status,
                "scan_time": att.scan_time.strftime("%H:%M:%S") if att.scan_time else "-",
                "block_index": att.block_index,
            })
        else:
            # Catat ABSEN ke DB
            absent_record = Attendance(
                student_id=student.id,
                session_id=session_id,
                status='absen',
                scan_time=scan_time_now,
            )
            db.add(absent_record)
            db.flush()  # Dapatkan ID agar bisa diupdate setelah mining

            # Buat blok blockchain untuk catatan absen
            block_data = {
                "student_id": student.id,
                "session_id": session_id,
                "status": "absen",
                "scan_time": scan_time_now.isoformat(),
                "recorded_by": "system_auto_close",
            }
            new_block = bc.add_block(block_data)
            absent_record.block_index = new_block.index

            recap.append({
                "nama": student.nama_lengkap,
                "nis": student.nis,
                "kelas": student.kelas,
                "status": "absen",
                "scan_time": scan_time_now.strftime("%H:%M:%S"),
                "block_index": new_block.index,
            })

    db.commit()
    return recap
