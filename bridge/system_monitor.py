from pathlib import Path
import time

import psutil


BYTES_PER_GB = 1024 ** 3
BYTES_PER_MB = 1024 ** 2


def bytes_to_gb(value: int) -> float:
    return round(value / BYTES_PER_GB, 2)


def seconds_to_readable(seconds: int) -> str:
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    return f"{days}d {hours}h {minutes}m"


def get_system_stats() -> dict:
    memory = psutil.virtual_memory()

    system_drive = Path.home().anchor or "C:\\"
    disk = psutil.disk_usage(system_drive)

    network = psutil.net_io_counters()

    uptime_seconds = int(
        time.time() - psutil.boot_time()
    )

    battery = psutil.sensors_battery()

    battery_data = None

    if battery is not None:
        battery_data = {
            "percent": round(battery.percent, 1),
            "charging": bool(battery.power_plugged),
        }

    return {
        "cpu": {
            "percent": round(
                psutil.cpu_percent(interval=0.2),
                1,
            ),
            "physical_cores": psutil.cpu_count(
                logical=False
            ),
            "logical_cores": psutil.cpu_count(
                logical=True
            ),
        },
        "memory": {
            "percent": round(memory.percent, 1),
            "used_gb": bytes_to_gb(memory.used),
            "available_gb": bytes_to_gb(
                memory.available
            ),
            "total_gb": bytes_to_gb(memory.total),
        },
        "disk": {
            "drive": system_drive,
            "percent": round(disk.percent, 1),
            "used_gb": bytes_to_gb(disk.used),
            "free_gb": bytes_to_gb(disk.free),
            "total_gb": bytes_to_gb(disk.total),
        },
        "network": {
            "sent_mb": round(
                network.bytes_sent / BYTES_PER_MB,
                1,
            ),
            "received_mb": round(
                network.bytes_recv / BYTES_PER_MB,
                1,
            ),
        },
        "battery": battery_data,
        "uptime": {
            "seconds": uptime_seconds,
            "readable": seconds_to_readable(
                uptime_seconds
            ),
        },
    }