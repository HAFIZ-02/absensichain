import bcrypt

def hash_password(password: str) -> str:
    """Hash password menggunakan algoritma bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Verifikasi kesesuaian password plain dengan hash."""
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
