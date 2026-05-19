import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://absenchain_user:123@localhost:5432/absenchain_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "f72088283ecc8970508d1602eddaafc3580f956dead21dc4859ed42df63441ac ")
    HMAC_SECRET = os.getenv("HMAC_SECRET", "ce05914c3a82e0c3b7623f4cc2a6f1d71d6653a3dcaa7ce590cbeee9a8a83da2")
