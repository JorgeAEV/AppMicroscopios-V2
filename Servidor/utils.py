import psutil
import subprocess

def get_raspberry_status():
    # Temperatura CPU
    try:
        temp_str = subprocess.check_output(['vcgencmd', 'measure_temp']).decode()
        temp_c = float(temp_str.replace("temp=","").replace("'C\n",""))
    except Exception:
        temp_c = None

    # CPU %
    cpu_percent = psutil.cpu_percent(interval=1)

    # RAM
    mem = psutil.virtual_memory()
    ram_used = mem.used / (1024 * 1024)  # MB
    ram_total = mem.total / (1024 * 1024)  # MB

    # Disco
    disk = psutil.disk_usage('/')
    disk_free_gb = disk.free / (1024 * 1024 * 1024)  # GB
    disk_used_gb = disk.used / (1024 * 1024 * 1024)  # GB

    return {
        'temperature_c': temp_c,
        'cpu_percent': cpu_percent,
        'ram_used_mb': round(ram_used,2),
        'ram_total_mb': round(ram_total,2),
        'disk_used_gb': round(disk_used_gb,2),
        'disk_free_gb': round(disk_free_gb,2)
    }
