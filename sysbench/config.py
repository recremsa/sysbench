import json
from pathlib import Path


CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)


def validate_config(config):
    required_sections = [
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "system_load",
        "latency_ms",
        "packet_loss_percent",
    ]

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing configuration section: {section}")

        thresholds = config[section]

        if "warning" not in thresholds or "fail" not in thresholds:
            raise ValueError(f"Missing thresholds in: {section}")

        warning = thresholds["warning"]
        fail = thresholds["fail"]

        if not isinstance(warning, (int, float)):
            raise ValueError(f"Warning threshold must be numeric: {section}")

        if not isinstance(fail, (int, float)):
            raise ValueError(f"Fail threshold must be numeric: {section}")

        if warning >= fail:
            raise ValueError(
                f"Warning threshold must be lower than fail: {section}"
            )

    return True


if __name__ == "__main__":
    config = load_config()
    validate_config(config)
    print("Configuration is valid")
    