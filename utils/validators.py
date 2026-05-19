import re

def validate_email_format(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
