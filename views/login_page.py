import streamlit as st
from database.connection import SessionLocal
from database.models import User
from auth.password_utils import verify_password

def render():
    st.title("🔐 Login AbsenChain")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Masuk"):
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            if user.status.lower() != 'active':
                st.error("Akun Anda belum dikonfirmasi oleh Admin (PENDING).")
            else:
                st.session_state['user_id'] = user.id
                st.session_state['role'] = user.role
                st.session_state['username'] = user.username
                st.success("Login berhasil!")
                st.rerun()
        else:
            st.error("Username atau password salah.")
        db.close()
