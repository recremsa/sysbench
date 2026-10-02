from sysbench.config import load_config, validate_config
from sysbench.cpu import get_cpu_metrics
from sysbench.disk import get_disk_metrics
from sysbench.load import get_load_metrics
from sysbench.memory import get_memory_metrics
from sysbench.network import get_ping_metrics
from sysbench.validation.validator import (
    get_overall_status,
    validate_cpu,
    validate_disk,
    validate_latency,
    validate_memory,
    validate_packet_loss,
    validate_system_load,
)


def collect_and_validate():
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

    overall_status = get_overall_status(statuses)

    return (
        cpu,
        memory,
        disk,
        load,
        network,
        statuses,
        overall_status,
    )
