def print_report(cpu, memory, disk, load, network, statuses, overall_status):
    (
        cpu_status,
        memory_status,
        disk_status,
        load_status,
        latency_status,
        packet_loss_status,
    ) = statuses

    print()
    print("╔══════════════════════════════════════════╗")
    print("║ SYSBENCH REPORT                          ║")
    print("╚══════════════════════════════════════════╝")

    print("SYSTEM")
    print(f"CPU Usage              {cpu['usage_percent']:.1f}%       {cpu_status}")
    print(f"Memory Usage           {memory['usage_percent']:.1f}%       {memory_status}")
    print(f"Disk Usage             {disk['usage_percent']:.1f}%       {disk_status}")
    print(f"System Load            {load['load_1min']:.2f}       {load_status}")

    print()
    print("NETWORK")
    print(
        f"Latency                "
        f"{network['latency_avg_ms']} ms      {latency_status}"
    )
    print(
        f"Packet Loss            "
        f"{network['packet_loss_percent']:.1f}%       {packet_loss_status}"
    )

    print()
    print("INTERFACE")

    for interface, data in network["interfaces"].items():
        print(f"Interface              {interface}")
        print(f"RX                     {data['bytes_received']} bytes")
        print(f"TX                     {data['bytes_sent']} bytes")
        print(f"Errors                 {data['errors']}")
        print(f"Drops                  {data['drops']}")
        print()

    print("──────────────────────────────────────────")
    print(f"SYSTEM STATUS: {overall_status}")
    print("──────────────────────────────────────────")


def print_network_report(network, latency_status, packet_loss_status, overall_status):
    print()
    print("╔══════════════════════════════════════════╗")
    print("║ SYSBENCH NETWORK REPORT                  ║")
    print("╚══════════════════════════════════════════╝")

    print("LATENCY & PACKET LOSS")
    if network["latency_avg_ms"] is not None:
        print(f"Latency Min            {network['latency_min_ms']} ms")
        print(f"Latency Avg            {network['latency_avg_ms']} ms      {latency_status}")
        print(f"Latency Max            {network['latency_max_ms']} ms")
    else:
        print("Latency Min            N/A")
        print(f"Latency Avg            N/A       {latency_status}")
        print("Latency Max            N/A")

    print(
        f"Packet Loss            "
        f"{network['packet_loss_percent']:.1f}%       {packet_loss_status}"
    )

    print()
    print("INTERFACE")

    for interface, data in network["interfaces"].items():
        print(f"Interface              {interface}")
        print(f"RX                     {data['bytes_received']} bytes")
        print(f"TX                     {data['bytes_sent']} bytes")
        print(f"Errors                 {data['errors']}")
        print(f"Drops                  {data['drops']}")
        print()

    print("──────────────────────────────────────────")
    print(f"NETWORK STATUS: {overall_status}")
    print("──────────────────────────────────────────")