import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from sysbench.reporting.plot import (
    create_metric_plot,
    extract_metric_data,
    plot_cpu_usage,
    plot_latency,
    plot_memory_usage,
    plot_network_latency,
    save_figure,
)


class TestPlot(unittest.TestCase):
    def setUp(self):
        self.sample_history = [
            {
                "timestamp": "2026-08-16T17:31:18.817504+00:00",
                "cpu_usage": 21.8,
                "memory_usage": 59.6,
                "disk_usage": 13.9,
                "load_average": 1.64,
                "latency_ms": 36.372,
                "packet_loss": 0.0,
                "status": "PASS",
            },
            {
                "timestamp": "2026-08-16T17:31:27.861527+00:00",
                "cpu_usage": 2.8,
                "memory_usage": 58.0,
                "disk_usage": 13.9,
                "load_average": 1.39,
                "latency_ms": 35.719,
                "packet_loss": 0.0,
                "status": "PASS",
            },
            {
                "timestamp": "2026-08-16T17:34:18.253077+00:00",
                "cpu_usage": 29.4,
                "memory_usage": 58.6,
                "disk_usage": 13.9,
                "load_average": 1.92,
                "latency_ms": 36.359,
                "packet_loss": 0.0,
                "status": "PASS",
            },
        ]

    def tearDown(self):
        plt.close("all")

    def test_extract_cpu_history(self):
        timestamps, values = extract_metric_data(self.sample_history, "cpu_usage")
        self.assertEqual(len(timestamps), 3)
        self.assertEqual(len(values), 3)
        self.assertEqual(timestamps[0], "2026-08-16T17:31:18.817504+00:00")
        self.assertEqual(values, [21.8, 2.8, 29.4])

    def test_extract_memory_history(self):
        timestamps, values = extract_metric_data(self.sample_history, "memory_usage")
        self.assertEqual(len(timestamps), 3)
        self.assertEqual(values, [59.6, 58.0, 58.6])

    def test_extract_latency_history(self):
        timestamps, values = extract_metric_data(self.sample_history, "latency_ms")
        self.assertEqual(len(timestamps), 3)
        self.assertEqual(values, [36.372, 35.719, 36.359])

    def test_extract_latency_with_none_and_missing(self):
        history_with_none = [
            {"timestamp": "2026-08-16T10:00:00", "latency_ms": 15.0},
            {"timestamp": "2026-08-16T10:00:05", "latency_ms": None},
            {"timestamp": "2026-08-16T10:00:10"},  # Missing latency_ms key
        ]
        timestamps, values = extract_metric_data(history_with_none, "latency_ms")
        self.assertEqual(timestamps, ["2026-08-16T10:00:00", "2026-08-16T10:00:05", "2026-08-16T10:00:10"])
        self.assertEqual(values, [15.0, None, None])

    def test_extract_empty_or_none_history(self):
        self.assertEqual(extract_metric_data([], "cpu_usage"), ([], []))
        self.assertEqual(extract_metric_data(None, "cpu_usage"), ([], []))

    def test_plot_cpu_usage_creates_figure(self):
        fig = plot_cpu_usage(self.sample_history)
        self.assertIsInstance(fig, Figure)
        self.assertEqual(len(fig.axes), 1)
        ax = fig.axes[0]
        self.assertEqual(ax.get_title(), "CPU Usage Trend")
        self.assertEqual(ax.get_ylabel(), "CPU Usage (%)")
        self.assertEqual(ax.get_xlabel(), "Time")
        # Verify 1 line plotted with 3 points
        lines = ax.get_lines()
        self.assertEqual(len(lines), 1)
        xdata = np.asarray(lines[0].get_xdata())
        self.assertEqual(len(xdata), 3)

    def test_plot_memory_usage_creates_figure(self):
        fig = plot_memory_usage(self.sample_history)
        self.assertIsInstance(fig, Figure)
        ax = fig.axes[0]
        self.assertEqual(ax.get_title(), "Memory Usage Trend")
        self.assertEqual(ax.get_ylabel(), "Memory Usage (%)")

    def test_plot_latency_creates_figure(self):
        fig = plot_latency(self.sample_history)
        self.assertIsInstance(fig, Figure)
        ax = fig.axes[0]
        self.assertEqual(ax.get_title(), "Network Latency Trend")
        self.assertEqual(ax.get_ylabel(), "Latency (ms)")

    def test_plot_network_latency_alias(self):
        fig = plot_network_latency(self.sample_history)
        self.assertIsInstance(fig, Figure)
        ax = fig.axes[0]
        self.assertEqual(ax.get_title(), "Network Latency Trend")

    def test_plot_latency_with_none_values_does_not_crash(self):
        mixed_latency_history = [
            {"timestamp": "2026-08-16T10:00:00", "latency_ms": 20.0},
            {"timestamp": "2026-08-16T10:00:05", "latency_ms": None},
            {"timestamp": "2026-08-16T10:00:10", "latency_ms": 25.0},
        ]
        fig = plot_latency(mixed_latency_history)
        self.assertIsInstance(fig, Figure)
        lines = fig.axes[0].get_lines()
        self.assertEqual(len(lines), 1)

        # Also test with ALL None values
        all_none_history = [
            {"timestamp": "2026-08-16T10:00:00", "latency_ms": None},
            {"timestamp": "2026-08-16T10:00:05", "latency_ms": None},
        ]
        fig_none = plot_latency(all_none_history)
        self.assertIsInstance(fig_none, Figure)

    def test_plot_empty_history_handled_deterministically(self):
        for plot_fn in (plot_cpu_usage, plot_memory_usage, plot_latency):
            # Test empty list
            fig_empty = plot_fn([])
            self.assertIsInstance(fig_empty, Figure)
            texts = [t.get_text() for t in fig_empty.axes[0].texts]
            self.assertIn("No data available", texts)

            # Test None input
            fig_none = plot_fn(None)
            self.assertIsInstance(fig_none, Figure)
            texts_none = [t.get_text() for t in fig_none.axes[0].texts]
            self.assertIn("No data available", texts_none)

    def test_save_figure_to_temp_path(self):
        fig = plot_cpu_usage(self.sample_history)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "test_cpu.png"
            save_figure(fig, output_file)
            self.assertTrue(output_file.exists())
            self.assertGreater(output_file.stat().st_size, 0)

    def test_plot_with_output_path_generates_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "subdir" / "test_memory.png"
            fig = plot_memory_usage(self.sample_history, output_path=output_file)
            self.assertIsInstance(fig, Figure)
            self.assertTrue(output_file.exists())
            self.assertGreater(output_file.stat().st_size, 0)

    @patch("sysbench.reporting.plot.plt.show")
    def test_no_gui_required_during_automated_tests(self, mock_show):
        fig = plot_cpu_usage(self.sample_history)
        self.assertIsInstance(fig, Figure)
        mock_show.assert_not_called()

    @patch("sysbench.reporting.plot.plt.show")
    def test_show_flag_triggers_plt_show(self, mock_show):
        fig = plot_cpu_usage(self.sample_history, show=True)
        self.assertIsInstance(fig, Figure)
        mock_show.assert_called_once()

    def test_create_metric_plot_direct(self):
        fig = create_metric_plot(
            self.sample_history,
            metric_key="cpu_usage",
            title="Custom Title",
            ylabel="Custom Y",
            color="red",
        )
        self.assertIsInstance(fig, Figure)


if __name__ == "__main__":
    unittest.main()
