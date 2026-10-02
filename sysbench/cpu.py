import psutil

def get_cpu_metrics():
    return{
        "usage_percent": psutil.cpu_percent(interval=1),
        "core_count" : psutil.cpu_count(logical=True),
        "load_average": psutil.getloadavg()[0],
    }

if __name__ == "__main__":
    print(get_cpu_metrics())