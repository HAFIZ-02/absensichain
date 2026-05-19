import streamlit as st
from database.models import BlockModel, Student
from blockchain.chain import Blockchain

def render_blockchain(db):
    st.subheader("Histori Ledger Blockchain")
    bc = Blockchain()
    is_valid, errors = bc.verify_chain()
    
    if is_valid: 
        st.success("Pemeriksaan Rantai Selesai: SELURUH BLOK VALID ✅")
    else: 
        st.error("Pemeriksaan Rantai Selesai: TERDETEKSI MANIPULASI (INVALID) ❌")
        for err in errors:
            st.warning(err)
        
    blocks = db.query(BlockModel).order_by(BlockModel.block_index.desc()).limit(50).all()
    
    for b in blocks:
        # Ekstrak status kehadiran dan ID Siswa dari JSON Data
        status_teks = ""
        nama_siswa = "Sistem"
        
        if b.block_index == 0:
            status_teks = "🌟 GENESIS BLOCK"
        else:
            data_dict = b.data if isinstance(b.data, dict) else {}
            
            # Ambil properti dari data JSON blok
            status = data_dict.get("status", "unknown").upper()
            student_id = data_dict.get("student_id")
            
            # Cocokkan ID dengan Nama Siswa di Database
            if student_id:
                student = db.query(Student).filter(Student.id == student_id).first()
                if student:
                    nama_siswa = student.nama_lengkap
            
            # Berikan Ikon sesuai status
            if status == "HADIR":
                icon = "✅"
            elif status == "TERLAMBAT":
                icon = "🕐"
            elif status == "ABSEN":
                icon = "❌"
            else:
                icon = "❓"
                
            status_teks = f"{icon} {nama_siswa} — {status}"

        # Judul Expander yang informatif
        expander_title = f"Blok #{b.block_index} | {status_teks} | Hash: {b.hash[:15]}..."
        
        with st.expander(expander_title):
            st.json({
                "timestamp": b.timestamp, 
                "previous_hash": b.previous_hash, 
                "nonce": b.nonce, 
                "data": b.data, 
                "validator_sig": b.validator_sig
            })
