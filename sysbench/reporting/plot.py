from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


def extract_metric_data(
    history: Optional[List[Dict[str, Any]]], metric_key: str
) -> Tuple[List[str], List[Any]]:
    """
    Extract timestamps and metric values from monitoring history records.

    Safely handles empty or None history and missing keys.
    """
    if not history:
        return [], []

    timestamps = [str(record.get("timestamp", "")) for record in history]
    values = [record.get(metric_key) for record in history]
    return timestamps, values


def save_figure(fig: Figure, output_path: Union[str, Path]) -> None:
    """
    Save a Matplotlib Figure to disk using the non-interactive Agg canvas engine.

    Ensures parent directories exist and guarantees headless-safe file export.
    """
    path = Path(output_path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)

    if not isinstance(getattr(fig, "canvas", None), FigureCanvasAgg):
        FigureCanvasAgg(fig)

    fig.savefig(str(path), bbox_inches="tight")


def create_metric_plot(
    history: Optional[List[Dict[str, Any]]],
    metric_key: str,
    title: str,
    ylabel: str,
    output_path: Optional[Union[str, Path]] = None,
    show: bool = False,
    color: Optional[str] = None,
) -> Figure:
    """
    Generate a time-series plot for a given metric key from monitoring history.

    Parameters:
        history: List of monitoring records (dictionaries).
        metric_key: The dictionary key for the metric (e.g., 'cpu_usage').
        title: Plot title string.
        ylabel: Y-axis label string.
        output_path: Optional file path to save the generated figure.
        show: If True, invokes plt.show() for interactive display.
        color: Optional line color.

    Returns:
        The created Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    timestamps, values = extract_metric_data(history, metric_key)

    if not timestamps:
        ax.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
            color="gray",
        )
    else:
        # Sanitize values: keep numeric values, treat None / unparseable as float('nan')
        sanitized_values: List[float] = []
        for v in values:
            if v is None:
                sanitized_values.append(float("nan"))
            else:
                try:
                    sanitized_values.append(float(v))
                except (ValueError, TypeError):
                    sanitized_values.append(float("nan"))

        kwargs: Dict[str, Any] = {"marker": "o"}
        if color is not None:
            kwargs["color"] = color

        ax.plot(timestamps, sanitized_values, **kwargs)
        ax.tick_params(axis="x", rotation=45)

    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.6)
    fig.tight_layout()

    if output_path:
        save_figure(fig, output_path)

    if show:
        plt.show()

    return fig


def plot_cpu_usage(
    history: Optional[List[Dict[str, Any]]],
    output_path: Optional[Union[str, Path]] = None,
    show: bool = False,
) -> Figure:
    """Plot CPU usage (%) over time."""
    return create_metric_plot(
        history=history,
        metric_key="cpu_usage",
        title="CPU Usage Trend",
        ylabel="CPU Usage (%)",
        output_path=output_path,
        show=show,
        color="#1f77b4",
    )


def plot_memory_usage(
    history: Optional[List[Dict[str, Any]]],
    output_path: Optional[Union[str, Path]] = None,
    show: bool = False,
) -> Figure:
    """Plot memory usage (%) over time."""
    return create_metric_plot(
        history=history,
        metric_key="memory_usage",
        title="Memory Usage Trend",
        ylabel="Memory Usage (%)",
        output_path=output_path,
        show=show,
        color="#ff7f0e",
    )


def plot_latency(
    history: Optional[List[Dict[str, Any]]],
    output_path: Optional[Union[str, Path]] = None,
    show: bool = False,
) -> Figure:
    """Plot network latency (ms) over time, safely handling None values."""
    return create_metric_plot(
        history=history,
        metric_key="latency_ms",
        title="Network Latency Trend",
        ylabel="Latency (ms)",
        output_path=output_path,
        show=show,
        color="#2ca02c",
    )


# Convenient alias for network latency plotting
plot_network_latency = plot_latency