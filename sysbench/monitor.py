import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from sysbench.core import collect_and_validate


def get_default_history_path() -> Path:
    """
    Determine the default monitoring history path.

    Prioritizes local 'monitor_history.json' in the current working directory
    (e.g., repository workspace), otherwise defaults to standard XDG user state:
    $XDG_STATE_HOME/sysbench/monitor_history.json (or ~/.local/state/sysbench/monitor_history.json).
    """
    cwd_path = Path("monitor_history.json")
    if cwd_path.is_file():
        return cwd_path

    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        base_dir = Path(xdg_state) / "sysbench"
    else:
        try:
            base_dir = Path.home() / ".local" / "state" / "sysbench"
        except (RuntimeError, KeyError):
            return cwd_path

    return base_dir / "monitor_history.json"


def resolve_history_path(path: Optional[Union[str, Path]] = None) -> Path:
    """Return explicit path as Path object or fallback to default history path."""
    if path is not None:
        return Path(path)
    return get_default_history_path()


def create_monitoring_record(results: Tuple[Any, ...]) -> Dict[str, Any]:
    (
        cpu,
        memory,
        disk,
        load,
        network,
        statuses,
        overall_status,
    ) = results

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_usage": cpu.get("usage_percent"),
        "memory_usage": memory.get("usage_percent"),
        "disk_usage": disk.get("usage_percent"),
        "load_average": load.get("load_1min"),
        "latency_ms": network.get("latency_avg_ms"),
        "packet_loss": network.get("packet_loss_percent"),
        "status": overall_status,
    }


def format_sample_summary(results: Tuple[Any, ...]) -> str:
    (
        cpu,
        memory,
        disk,
        load,
        network,
        statuses,
        overall_status,
    ) = results

    cpu_val = cpu.get("usage_percent")
    cpu_str = f"{cpu_val:.1f}%" if isinstance(cpu_val, (int, float)) else "N/A"

    mem_val = memory.get("usage_percent")
    mem_str = f"{mem_val:.1f}%" if isinstance(mem_val, (int, float)) else "N/A"

    disk_val = disk.get("usage_percent")
    disk_str = f"{disk_val:.1f}%" if isinstance(disk_val, (int, float)) else "N/A"

    load_val = load.get("load_1min")
    load_str = f"{load_val:.2f}" if isinstance(load_val, (int, float)) else "N/A"

    lat_val = network.get("latency_avg_ms")
    lat_str = f"{lat_val} ms" if lat_val is not None else "N/A"

    loss_val = network.get("packet_loss_percent")
    loss_str = f"{loss_val:.1f}%" if isinstance(loss_val, (int, float)) else "N/A"

    return (
        f"CPU: {cpu_str} | "
        f"Memory: {mem_str} | "
        f"Disk: {disk_str} | "
        f"Load: {load_str} | "
        f"Latency: {lat_str} | "
        f"Loss: {loss_str} | "
        f"Status: {overall_status}"
    )


def load_monitoring_history(
    path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    Load monitoring records safely from disk.

    Handles missing files, malformed JSON, non-list root structure,
    and OS/permission errors gracefully.
    """
    target = resolve_history_path(path)
    if not target.exists():
        return []

    try:
        with open(target, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            print(
                f"Warning: History file '{target}' does not contain a JSON array; starting fresh.",
                file=sys.stderr,
            )
            return []
    except (json.JSONDecodeError, OSError) as err:
        print(
            f"Warning: Could not read history file '{target}': {err}; starting fresh.",
            file=sys.stderr,
        )
        return []


def save_monitoring_history(
    history: List[Dict[str, Any]],
    path: Optional[Union[str, Path]] = None,
) -> bool:
    """
    Save monitoring history records to disk.

    Ensures parent directories exist and handles permission/OS errors cleanly.
    Returns True if successfully written, False otherwise.
    """
    target = resolve_history_path(path)
    try:
        if target.parent:
            target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=2)
        return True
    except OSError as err:
        print(
            f"Error: Unable to save monitoring history to '{target}': {err}",
            file=sys.stderr,
        )
        return False


def run_monitor(
    interval: float = 5.0,
    history_path: Optional[Union[str, Path]] = None,
    max_iterations: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Run continuous performance monitor and record history.

    Parameters:
        interval: Sampling interval in seconds (start-to-start timing).
        history_path: Optional custom path for monitor history JSON.
        max_iterations: Optional limit on collection iterations (useful for testing).

    Returns:
        The updated history list.
    """
    resolved_path = resolve_history_path(history_path)
    print("SysBench monitoring started")
    print(f"Collection interval: {interval} seconds")
    print("Press Ctrl+C to stop.\n")

    history = load_monitoring_history(resolved_path)
    iterations = 0

    try:
        while max_iterations is None or iterations < max_iterations:
            loop_start = time.monotonic()

            try:
                results = collect_and_validate()
                record = create_monitoring_record(results)
                history.append(record)
                print(format_sample_summary(results))
            except Exception as err:
                print(f"Warning: Metric collection failed: {err}", file=sys.stderr)

            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break

            elapsed = time.monotonic() - loop_start
            sleep_duration = max(0.0, float(interval) - elapsed)
            time.sleep(sleep_duration)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

    print(f"Records collected: {len(history)}")
    if save_monitoring_history(history, resolved_path):
        print(f"Monitoring history saved to {resolved_path}")

    return history


if __name__ == "__main__":
    run_monitor()