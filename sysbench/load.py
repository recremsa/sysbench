import psutil


def get_load_metrics():
    load_1, load_5, load_15 = psutil.getloadavg()

    return {
        "load_1min": load_1,
        "load_5min": load_5,
        "load_15min": load_15,
    }


if __name__ == "__main__":
    print(get_load_metrics())