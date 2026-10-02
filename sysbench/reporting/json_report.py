import json
from datetime import datetime, timezone


def generate_json_report(
    cpu,
    memory,
    disk,
    load,
    network,
    statuses,
    overall_status,
):
    (
        cpu_status,
        memory_status,
        disk_status,
        load_status,
        latency_status,
        packet_loss_status,
    ) = statuses

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu": {
            "usage_percent": cpu["usage_percent"],
            "status": cpu_status,
        },
        "memory": {
            "usage_percent": memory["usage_percent"],
            "status": memory_status,
        },
        "disk": {
            "usage_percent": disk["usage_percent"],
            "status": disk_status,
        },
        "system_load": {
            "load_1min": load["load_1min"],
            "status": load_status,
        },
        "network": {
            "latency_min_ms": network["latency_min_ms"],
            "latency_avg_ms": network["latency_avg_ms"],
            "latency_max_ms": network["latency_max_ms"],
            "packet_loss_percent": network["packet_loss_percent"],
            "latency_status": latency_status,
            "packet_loss_status": packet_loss_status,
        },
        "interfaces": network["interfaces"],
        "status": overall_status,
    }


def print_json_report(
    cpu,
    memory,
    disk,
    load,
    network,
    statuses,
    overall_status,
):
    report = generate_json_report(
        cpu,
        memory,
        disk,
        load,
        network,
        statuses,
        overall_status,
    )

    print(json.dumps(report, indent=2))