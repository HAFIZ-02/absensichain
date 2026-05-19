from datetime import datetime, time
from database.models import Session

def determine_status(session: Session, scan_time: datetime) -> str:
    # Handle session.jam_mulai yang mungkin str atau datetime.time
    if isinstance(session.jam_mulai, time):
        start_time = datetime.combine(scan_time.date(), session.jam_mulai)
    else:
        parts = str(session.jam_mulai).split(":")
        start_time = datetime.combine(scan_time.date(), time(int(parts[0]), int(parts[1])))
    
    diff_mins = (scan_time - start_time).total_seconds() / 60.0
    if diff_mins > session.batas_terlambat_menit:
        return "terlambat"
    return "hadir"
