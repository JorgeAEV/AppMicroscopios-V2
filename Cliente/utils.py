from datetime import datetime

def format_bytes(size):
    # Convierte tamaño en bytes a KB, MB o GB legible
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def format_duration(seconds):
    # Convierte segundos a formato HH:MM:SS
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def timestamp_now():
    return datetime.now().strftime("%Y%m%d_%H%M%S")
