# system_monitor.py
import psutil
import shutil
import os

def get_cpu_usage():
    return psutil.cpu_percent(interval=0.5)

def get_ram_usage():
    mem = psutil.virtual_memory()
    return mem.used // (1024 ** 2), mem.total // (1024 ** 2)

def get_disk_space():
    total, used, free = shutil.disk_usage(os.path.expanduser("~"))
    return free // (1024 ** 2), free // (1024 ** 3)

def get_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000
        return temp
    except:
        return -1
