import psutil


def get_disk_metrics():
    disk = psutil.disk_usage("/")

    return {
        "total": disk.total,
        "used": disk.used,
        "available": disk.free,
        "usage_percent": disk.percent,
    }


if __name__ == "__main__":
    print(get_disk_metrics())