from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.connection import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    student = relationship("Student", back_populates="user", uselist=False)

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    nama_lengkap = Column(String, nullable=False)
    nis = Column(String, unique=True, index=True, nullable=False)
    kelas = Column(String, nullable=False)
    jenis_kelamin = Column(String, nullable=False)
    user = relationship("User", back_populates="student")
    qr_code = relationship("QRCode", back_populates="student", uselist=False)

class QRCode(Base):
    __tablename__ = 'qr_codes'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'), unique=True)
    payload_encrypted = Column(Text, nullable=False)
    qr_image_b64 = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    student = relationship("Student", back_populates="qr_code")

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, index=True)
    mapel = Column(String, nullable=False)
    kelas = Column(String, nullable=False)
    tanggal = Column(DateTime, nullable=False)
    jam_mulai = Column(String, nullable=False)
    jam_selesai = Column(String, nullable=False)
    batas_terlambat_menit = Column(Integer, default=15)
    status = Column(String, default='open')
    created_by = Column(Integer, ForeignKey('users.id'))

class Attendance(Base):
    __tablename__ = 'attendances'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    session_id = Column(Integer, ForeignKey('sessions.id'))
    status = Column(String, nullable=False)
    scan_time = Column(DateTime)
    block_index = Column(Integer)
    __table_args__ = (UniqueConstraint('student_id', 'session_id', name='_student_session_uc'),)

class BlockModel(Base):
    __tablename__ = 'blocks'
    id = Column(Integer, primary_key=True, index=True)
    block_index = Column(Integer, unique=True, nullable=False)
    timestamp = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    previous_hash = Column(String, nullable=False)
    nonce = Column(Integer, nullable=False)
    hash = Column(String, nullable=False)
    merkle_root = Column(String, nullable=False)
    validator_sig = Column(String, nullable=False)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String, nullable=False)
    detail = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
