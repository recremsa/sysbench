import re
import subprocess

import psutil


def get_interface_metrics():
    interfaces = {}

    stats = psutil.net_io_counters(pernic=True)

    for interface, data in stats.items():
        interfaces[interface] = {
            "bytes_sent": data.bytes_sent,
            "bytes_received": data.bytes_recv,
            "packets_sent": data.packets_sent,
            "packets_received": data.packets_recv,
            "errors": data.errin + data.errout,
            "drops": data.dropin + data.dropout,
        }

    return interfaces


def get_ping_metrics(host="1.1.1.1", count=4):
    result = subprocess.run(
        ["ping", "-c", str(count), host],
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout + result.stderr

    packet_match = re.search(
        r"(\d+) packets transmitted, (\d+) received, ([\d.]+)% packet loss",
        output,
    )

    rtt_match = re.search(
        r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms",
        output,
    )

    if not packet_match:
        raise RuntimeError("Unable to parse packet loss from ping output")

    packet_loss = float(packet_match.group(3))
    interfaces = get_interface_metrics()

    if not rtt_match:
        return {
            "latency_min_ms": None,
            "latency_avg_ms": None,
            "latency_max_ms": None,
            "packet_loss_percent": packet_loss,
            "interfaces": interfaces,
        }

    return {
        "latency_min_ms": float(rtt_match.group(1)),
        "latency_avg_ms": float(rtt_match.group(2)),
        "latency_max_ms": float(rtt_match.group(3)),
        "packet_loss_percent": packet_loss,
        "interfaces": interfaces,
    }


if __name__ == "__main__":
    print(get_interface_metrics())
    print(get_ping_metrics())