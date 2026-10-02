import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from sysbench.config import load_config, validate_config
from sysbench.core import collect_and_validate
from sysbench.monitor import get_default_history_path, run_monitor
from sysbench.network import get_ping_metrics
from sysbench.reporting.console import print_network_report, print_report
from sysbench.reporting.json_report import print_json_report
from sysbench.reporting.plot import (
    plot_cpu_usage,
    plot_latency,
    plot_memory_usage,
)
from sysbench.validation.validator import (
    get_overall_status,
    validate_latency,
    validate_packet_loss,
)


def run_check() -> None:
    results = collect_and_validate()
    print_report(*results)


def run_report() -> None:
    results = collect_and_validate()
    print_json_report(*results)


def run_network() -> Tuple[Dict[str, Any], str, str, str]:
    config = load_config()
    validate_config(config)

    network = get_ping_metrics()
    latency_status = validate_latency(network, config)
    packet_loss_status = validate_packet_loss(network, config)
    overall_status = get_overall_status([latency_status, packet_loss_status])

    print_network_report(network, latency_status, packet_loss_status, overall_status)
    return network, latency_status, packet_loss_status, overall_status


def derive_metric_output_path(base_output: Union[str, Path], metric: str) -> Path:
    """
    Derive a deterministic metric-specific output filename.

    Example:
        base_output='report.png', metric='cpu' -> 'report_cpu.png'
    """
    path = Path(base_output)
    ext = path.suffix if path.suffix else ".png"
    return path.parent / f"{path.stem}_{metric}{ext}"


def load_history_for_plot(
    history_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    Load monitoring records from a history JSON file.

    Validates file existence, JSON syntax, and list structure.
    """
    path = Path(history_path) if history_path else get_default_history_path()

    if history_path is not None and not path.exists():
        raise FileNotFoundError(f"History file not found: '{history_path}'")

    if not path.exists():
        # Default history file does not exist yet; return empty list
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as err:
        raise ValueError(f"History file '{path}' contains invalid JSON: {err}")
    except Exception as err:
        raise ValueError(f"Unable to read history file '{path}': {err}")

    if not isinstance(data, list):
        raise ValueError(
            f"History file '{path}' must contain a JSON list of records."
        )

    return data


def run_plot(
    metric: str = "all",
    output: Optional[Union[str, Path]] = None,
    history_path: Optional[Union[str, Path]] = None,
    show: Optional[bool] = None,
) -> Optional[List[Figure]]:
    """
    Execute performance visualization for CPU, memory, latency, or all metrics.

    Parameters:
        metric: One of 'cpu', 'memory', 'latency', or 'all'.
        output: Target output path. For 'all', metric suffixes are derived.
        history_path: Custom monitoring history JSON path.
        show: Whether to invoke plt.show(). Defaults to True if output is None.
    """
    if metric not in ("cpu", "memory", "latency", "all"):
        print(
            f"Error: Invalid metric '{metric}'. Choices are: cpu, memory, latency, all.",
            file=sys.stderr,
        )
        return None

    try:
        history = load_history_for_plot(history_path)
    except (FileNotFoundError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr, flush=True)
        return None

    is_show: bool = (output is None) if show is None else bool(show)

    figures: List[Figure] = []

    if metric == "cpu":
        fig = plot_cpu_usage(history, output_path=output, show=is_show)
        if output:
            print(f"Saved CPU usage plot to {output}")
        figures.append(fig)

    elif metric == "memory":
        fig = plot_memory_usage(history, output_path=output, show=is_show)
        if output:
            print(f"Saved memory usage plot to {output}")
        figures.append(fig)

    elif metric == "latency":
        fig = plot_latency(history, output_path=output, show=is_show)
        if output:
            print(f"Saved network latency plot to {output}")
        figures.append(fig)

    elif metric == "all":
        if output:
            cpu_out = derive_metric_output_path(output, "cpu")
            mem_out = derive_metric_output_path(output, "memory")
            lat_out = derive_metric_output_path(output, "latency")

            fig_cpu = plot_cpu_usage(history, output_path=cpu_out, show=False)
            fig_mem = plot_memory_usage(history, output_path=mem_out, show=False)
            fig_lat = plot_latency(history, output_path=lat_out, show=False)

            print(f"Saved CPU usage plot to {cpu_out}")
            print(f"Saved memory usage plot to {mem_out}")
            print(f"Saved network latency plot to {lat_out}")

            figures.extend([fig_cpu, fig_mem, fig_lat])
        else:
            fig_cpu = plot_cpu_usage(history, output_path=None, show=False)
            fig_mem = plot_memory_usage(history, output_path=None, show=False)
            fig_lat = plot_latency(history, output_path=None, show=False)
            figures.extend([fig_cpu, fig_mem, fig_lat])

        if is_show:
            plt.show()

    return figures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sysbench",
        description="Linux system performance analyzer and monitoring validation tool.",
        epilog=(
            "Available commands:\n"
            "  check     Run full system validation check and output tabular report\n"
            "  report    Generate structured JSON performance report\n"
            "  monitor   Run continuous performance monitor and record history\n"
            "  network   Run network ping latency and interface diagnostics\n"
            "  plot      Generate metric trend visualization plots\n\n"
            "Plot usage:\n"
            "  sysbench plot [metric] [--output PATH] [--history PATH]\n"
            "  metric choices: cpu, memory, latency, all (default: all)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to execute",
    )

    # Subcommand: check
    subparsers.add_parser(
        "check",
        help="Run full system validation check and output tabular report",
    )

    # Subcommand: report
    subparsers.add_parser(
        "report",
        help="Generate structured JSON performance report",
    )

    # Subcommand: monitor
    subparsers.add_parser(
        "monitor",
        help="Run continuous performance monitor and record history",
    )

    # Subcommand: network
    subparsers.add_parser(
        "network",
        help="Run network ping latency and interface diagnostics",
    )

    # Subcommand: plot
    plot_parser = subparsers.add_parser(
        "plot",
        help="Generate performance visualization plots from monitoring history",
        description="Plot CPU, memory, or network latency trends from monitoring history.",
    )
    plot_parser.add_argument(
        "metric",
        nargs="?",
        choices=["cpu", "memory", "latency", "all"],
        default=None,
        metavar="metric",
        help="Metric to plot: cpu, memory, latency, or all (default: all)",
    )
    plot_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to save output plot figure(s)",
    )
    plot_parser.add_argument(
        "--history",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to monitoring history JSON file (default: monitor_history.json)",
    )
    plot_parser.add_argument(
        "--metric",
        choices=["cpu", "memory", "latency", "all"],
        default=None,
        dest="flag_metric",
        help="Optional flag for metric to plot (backward compatibility)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(2)

    if args.command == "check":
        run_check()
    elif args.command == "report":
        run_report()
    elif args.command == "monitor":
        run_monitor()
    elif args.command == "network":
        run_network()
    elif args.command == "plot":
        pos_metric: Optional[str] = getattr(args, "metric", None)
        flag_metric: Optional[str] = getattr(args, "flag_metric", None)
        metric: str = pos_metric or flag_metric or "all"
        output: Optional[str] = getattr(args, "output", None)
        history_path: Optional[str] = getattr(args, "history", None)
        figs = run_plot(
            metric=metric,
            output=output,
            history_path=history_path,
        )
        if figs is None:
            sys.exit(1)


if __name__ == "__main__":
    main()