import streamlit as st
import pandas as pd
from database.connection import SessionLocal
from database.models import Student, Attendance, BlockModel
from components.badge_widget import render_badge
from components.qr_display import show_qr

def render():
    st.title(f"🎓 Dashboard Siswa")
    db = SessionLocal()
    student = db.query(Student).filter_by(user_id=st.session_state.user_id).first()
    
    if not student:
        st.error("Terjadi masalah sistem: Data siswa tidak ditemukan.")
        return
        
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    
    tab1, tab2, tab3 = st.tabs(["Identitas & QR", "Statistik", "Blockchain Data"])
    
    with tab1:
        st.write(f"**Nama:** {student.nama_lengkap} | **NIS:** {student.nis} | **Kelas:** {student.kelas}")
        if student.qr_code: show_qr(student.qr_code.qr_image_b64)
        else: st.warning("QR Code sedang disiapkan oleh sistem.")
            
    with tab2:
        atts = db.query(Attendance).filter_by(student_id=student.id).all()
        if not atts:
            st.info("Belum ada data kehadiran.")
        else:
            df = pd.DataFrame([{"Status": a.status.capitalize()} for a in atts])
            counts = df['Status'].value_counts()
            total = len(atts)
            hadir = counts.get('Hadir', 0) + counts.get('Terlambat', 0)
            perc = (hadir / total) * 100 if total > 0 else 0
            
            render_badge(perc)
            st.bar_chart(counts)
            
    with tab3:
        all_blocks = db.query(BlockModel).all()
        blocks = [b for b in all_blocks if str(b.data.get('student_id')) == str(student.id)]
        for b in blocks:
            st.code(f"ID Transaksi: {b.hash}\nWaktu Catat: {b.timestamp}\nStatus Masuk: {b.data.get('status')}")
    db.close()
