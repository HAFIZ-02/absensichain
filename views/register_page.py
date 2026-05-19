import streamlit as st
from database.connection import SessionLocal
from database.models import User, Student
from auth.password_utils import hash_password

def render():
    st.title("📝 Registrasi Siswa Baru")
    nama = st.text_input("Nama Lengkap")
    nis = st.text_input("NIS")
    kelas = st.selectbox("Kelas", ["10A", "10B", "11A", "11B", "12A", "12B"])
    jk = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    username = st.text_input("Username (wajib diakhiri dengan @siswa)")
    password = st.text_input("Password", type="password")
    
    if st.button("Daftar"):
        if not username.endswith("@siswa"):
            st.error("Username siswa harus memiliki suffix @siswa (contoh: budi@siswa)")
            return
            
        db = SessionLocal()
        if db.query(User).filter_by(username=username).first():
            st.error("Username sudah terdaftar.")
        elif db.query(Student).filter_by(nis=nis).first():
            st.error("NIS sudah terdaftar.")
        else:
            new_user = User(username=username, password_hash=hash_password(password), role='siswa')
            db.add(new_user)
            db.commit()
            new_student = Student(user_id=new_user.id, nama_lengkap=nama, nis=nis, kelas=kelas, jenis_kelamin=jk)
            db.add(new_student)
            db.commit()
            st.success("Registrasi berhasil! Silahkan tunggu konfirmasi dari Admin.")
        db.close()
