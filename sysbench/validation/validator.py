from sysbench.config import load_config, validate_config


def validate_metric(value, warning_threshold, fail_threshold):
    if value >= fail_threshold:
        return "FAIL"

    if value >= warning_threshold:
        return "WARNING"

    return "PASS"


def validate_cpu(cpu_metrics, config):
    thresholds = config["cpu_usage"]

    return validate_metric(
        cpu_metrics["usage_percent"],
        thresholds["warning"],
        thresholds["fail"],
    )


def validate_memory(memory_metrics, config):
    thresholds = config["memory_usage"]

    return validate_metric(
        memory_metrics["usage_percent"],
        thresholds["warning"],
        thresholds["fail"],
    )


def validate_disk(disk_metrics, config):
    thresholds = config["disk_usage"]

    return validate_metric(
        disk_metrics["usage_percent"],
        thresholds["warning"],
        thresholds["fail"],
    )

def validate_system_load(load_metrics, cpu_metrics, config):
    thresholds = config["system_load"]

    load_ratio = load_metrics["load_1min"] / cpu_metrics["core_count"]

    return validate_metric(
        load_ratio,
        thresholds["warning"],
        thresholds["fail"],
    )

def validate_latency(network_metrics, config):
    thresholds = config["latency_ms"]

    latency = network_metrics["latency_avg_ms"]

    if latency is None:
        return "FAIL"

    return validate_metric(
        latency,
        thresholds["warning"],
        thresholds["fail"],
    )

def validate_packet_loss(network_metrics, config):
    thresholds = config["packet_loss_percent"]

    return validate_metric(
        network_metrics["packet_loss_percent"],
        thresholds["warning"],
        thresholds["fail"],
    )

def get_overall_status(statuses):
    if "FAIL" in statuses:
        return "FAIL"

    if "WARNING" in statuses:
        return "WARNING"

    return "PASS"

if __name__ == "__main__":
    from sysbench.network import get_ping_metrics
    from sysbench.cpu import get_cpu_metrics
    from sysbench.memory import get_memory_metrics
    from sysbench.disk import get_disk_metrics
    from sysbench.load import get_load_metrics

    config = load_config()
    validate_config(config)

    cpu = get_cpu_metrics()
    memory = get_memory_metrics()
    disk = get_disk_metrics()
    load = get_load_metrics()
    network = get_ping_metrics()

    cpu_status = validate_cpu(cpu, config)
    memory_status = validate_memory(memory, config)
    disk_status = validate_disk(disk, config)
    load_status = validate_system_load(load, cpu, config)
    latency_status = validate_latency(network, config)
    packet_loss_status = validate_packet_loss(network, config)

    statuses = [
        cpu_status,
        memory_status,
        disk_status,
        load_status,
        latency_status,
        packet_loss_status,
    ]

    print(f"CPU Usage: {cpu['usage_percent']}%")
    print(f"CPU Status: {cpu_status}")

    print(f"Memory Usage: {memory['usage_percent']}%")
    print(f"Memory Status: {memory_status}")

    print(f"Disk Usage: {disk['usage_percent']}%")
    print(f"Disk Status: {disk_status}")

    print(f"System Load: {load['load_1min']}")
    print(f"Load Status: {load_status}")

    print(f"Average Latency: {network['latency_avg_ms']} ms")
    print(f"Latency Status: {latency_status}")

    print(f"Packet Loss: {network['packet_loss_percent']}%")
    print(f"Packet Loss Status: {packet_loss_status}")

    print(f"System Status: {get_overall_status(statuses)}")