import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Cek konfigurasi database (Supabase Cloud vs Lokal)
if "postgres" in st.secrets:
    pg = st.secrets["postgres"]
    # Menyusun secara aman meskipun password mengandung karakter '@'
    DATABASE_URL = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"
else:
    # Jika dijalankan di laptop sendiri, arahkan ke localhost kamu
    DATABASE_URL = "postgresql://postgres:hpzKDRI@_245@localhost:5432/postgres"

# 2. Buat engine SQLAlchemy dengan URL yang sesuai
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3. Buat Session dan Base seperti semula
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
