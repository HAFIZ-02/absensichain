from datetime import datetime, timezone

def get_current_utc():
    return datetime.now(timezone.utc)
