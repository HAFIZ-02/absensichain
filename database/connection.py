import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import urllib.parse

# 1. Cek konfigurasi database (Supabase Cloud vs Lokal)
if "postgres" in st.secrets:
    pg = st.secrets["postgres"]
    # Mengamankan password Cloud jika di secrets ditulis pakai '@'
    safe_password = urllib.parse.quote_plus(pg['password'])
    DATABASE_URL = f"postgresql://{pg['user']}:{safe_password}@{pg['host']}:{pg['port']}/{pg['database']}"
else:
    # Mengamankan password Lokal kamu yang mengandung karakter '@'
    # 'hpzKDRI@_245' akan diubah otomatis oleh sistem menjadi 'hpzKDRI%40_245'
    safe_password = urllib.parse.quote_plus("hpzKDRI@_245")
    DATABASE_URL = f"postgresql://postgres:{safe_password}@localhost:5432/postgres"

# 2. Buat engine SQLAlchemy dengan URL yang sesuai
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3. Buat Session dan Base seperti semula
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
