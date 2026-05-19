import streamlit as st
from database.connection import engine, Base, SessionLocal
from database.models import User
from auth.password_utils import hash_password
from views import login_page, register_page, student_dashboard, admin_dashboard

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Otomatis buat akun admin pertama kali dijalankan
    if not db.query(User).filter_by(username="admin@admin").first():
        admin = User(username="admin@admin", password_hash=hash_password("admin123"), role="admin", status="active")
        db.add(admin)
        db.commit()
    db.close()

def main():
    st.set_page_config(page_title="AbsenChain WebApp", page_icon="🔗", layout="wide")
    init_db()

    if 'user_id' not in st.session_state:
        st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/1200px-Bitcoin.svg.png", width=50)
        st.sidebar.title("Navigasi Sistem")
        choice = st.sidebar.radio("Silahkan Pilih", ["Masuk", "Registrasi"])
        if choice == "Masuk": login_page.render()
        else: register_page.render()
    else:
        if st.session_state.role == 'admin': admin_dashboard.render()
        else: student_dashboard.render()

if __name__ == "__main__":
    main()
