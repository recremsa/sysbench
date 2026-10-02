import psutil


def get_memory_metrics():
    memory = psutil.virtual_memory()

    return {
        "total": memory.total,
        "used": memory.used,
        "available": memory.available,
        "usage_percent": memory.percent,
    }


if __name__ == "__main__":
    print(get_memory_metrics())
    