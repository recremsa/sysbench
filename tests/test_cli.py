import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt

from sysbench.cli import (
    build_parser,
    derive_metric_output_path,
    main,
    run_network,
    run_plot,
)


class TestCLINetwork(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            "cpu_usage": {"warning": 75, "fail": 90},
            "memory_usage": {"warning": 75, "fail": 90},
            "disk_usage": {"warning": 80, "fail": 95},
            "system_load": {"warning": 1.0, "fail": 1.5},
            "latency_ms": {"warning": 50, "fail": 100},
            "packet_loss_percent": {"warning": 1, "fail": 5},
        }
        self.mock_network_pass = {
            "latency_min_ms": 12.0,
            "latency_avg_ms": 15.0,
            "latency_max_ms": 18.0,
            "packet_loss_percent": 0.0,
            "interfaces": {
                "eth0": {
                    "bytes_sent": 100000,
                    "bytes_received": 200000,
                    "packets_sent": 100,
                    "packets_received": 200,
                    "errors": 0,
                    "drops": 0,
                },
                "wlan0": {
                    "bytes_sent": 50000,
                    "bytes_received": 80000,
                    "packets_sent": 40,
                    "packets_received": 60,
                    "errors": 2,
                    "drops": 3,
                },
            },
        }

    @patch("sysbench.cli.print_network_report")
    @patch("sysbench.cli.get_ping_metrics")
    @patch("sysbench.cli.validate_config")
    @patch("sysbench.cli.load_config")
    def test_run_network_successful_pass(
        self, mock_load, mock_val, mock_get_ping, mock_print
    ):
        mock_load.return_value = self.mock_config
        mock_val.return_value = True
        mock_get_ping.return_value = self.mock_network_pass

        network, lat_stat, loss_stat, overall = run_network()

        self.assertEqual(lat_stat, "PASS")
        self.assertEqual(loss_stat, "PASS")
        self.assertEqual(overall, "PASS")
        mock_print.assert_called_once_with(
            self.mock_network_pass, "PASS", "PASS", "PASS"
        )

    @patch("sysbench.cli.print_network_report")
    @patch("sysbench.cli.get_ping_metrics")
    @patch("sysbench.cli.validate_config")
    @patch("sysbench.cli.load_config")
    def test_run_network_warning_latency(
        self, mock_load, mock_val, mock_get_ping, mock_print
    ):
        mock_load.return_value = self.mock_config
        mock_val.return_value = True
        net_warning = dict(self.mock_network_pass, latency_avg_ms=65.0)
        mock_get_ping.return_value = net_warning

        network, lat_stat, loss_stat, overall = run_network()

        self.assertEqual(lat_stat, "WARNING")
        self.assertEqual(loss_stat, "PASS")
        self.assertEqual(overall, "WARNING")
        mock_print.assert_called_once_with(
            net_warning, "WARNING", "PASS", "WARNING"
        )

    @patch("sysbench.cli.print_network_report")
    @patch("sysbench.cli.get_ping_metrics")
    @patch("sysbench.cli.validate_config")
    @patch("sysbench.cli.load_config")
    def test_run_network_fail_packet_loss(
        self, mock_load, mock_val, mock_get_ping, mock_print
    ):
        mock_load.return_value = self.mock_config
        mock_val.return_value = True
        net_fail = dict(self.mock_network_pass, packet_loss_percent=8.0)
        mock_get_ping.return_value = net_fail

        network, lat_stat, loss_stat, overall = run_network()

        self.assertEqual(lat_stat, "PASS")
        self.assertEqual(loss_stat, "FAIL")
        self.assertEqual(overall, "FAIL")
        mock_print.assert_called_once_with(
            net_fail, "PASS", "FAIL", "FAIL"
        )

    @patch("sysbench.cli.get_ping_metrics")
    @patch("sysbench.cli.validate_config")
    @patch("sysbench.cli.load_config")
    def test_run_network_interface_statistics_and_report_rendering(
        self, mock_load, mock_val, mock_get_ping
    ):
        mock_load.return_value = self.mock_config
        mock_val.return_value = True
        mock_get_ping.return_value = self.mock_network_pass

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            run_network()

        output = captured_stdout.getvalue()

        # Check section headers
        self.assertIn("SYSBENCH NETWORK REPORT", output)
        self.assertIn("LATENCY & PACKET LOSS", output)
        self.assertIn("INTERFACE", output)

        # Check latency statistics
        self.assertIn("Latency Min            12.0 ms", output)
        self.assertIn("Latency Avg            15.0 ms      PASS", output)
        self.assertIn("Latency Max            18.0 ms", output)
        self.assertIn("Packet Loss            0.0%       PASS", output)

        # Check interface rendering
        self.assertIn("Interface              eth0", output)
        self.assertIn("RX                     200000 bytes", output)
        self.assertIn("TX                     100000 bytes", output)
        self.assertIn("Interface              wlan0", output)
        self.assertIn("Errors                 2", output)
        self.assertIn("Drops                  3", output)

        # Check overall network status
        self.assertIn("NETWORK STATUS: PASS", output)


class TestCLIDispatch(unittest.TestCase):
    @patch("sysbench.cli.run_check")
    @patch("sys.argv", ["sysbench", "check"])
    def test_main_check_command_dispatched(self, mock_run_check):
        main()
        mock_run_check.assert_called_once()

    @patch("sysbench.cli.run_report")
    @patch("sys.argv", ["sysbench", "report"])
    def test_main_report_command_dispatched(self, mock_run_report):
        main()
        mock_run_report.assert_called_once()

    @patch("sysbench.cli.run_monitor")
    @patch("sys.argv", ["sysbench", "monitor"])
    def test_main_monitor_command_dispatched(self, mock_run_monitor):
        main()
        mock_run_monitor.assert_called_once()

    @patch("sysbench.cli.run_network")
    @patch("sys.argv", ["sysbench", "network"])
    def test_main_network_command_dispatched(self, mock_run_network):
        main()
        mock_run_network.assert_called_once()

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot"])
    def test_main_plot_default_dispatches_all(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="all", output=None, history_path=None
        )

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot", "cpu"])
    def test_main_plot_positional_cpu(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="cpu", output=None, history_path=None
        )

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot", "memory"])
    def test_main_plot_positional_memory(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="memory", output=None, history_path=None
        )

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot", "latency"])
    def test_main_plot_positional_latency(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="latency", output=None, history_path=None
        )

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot", "all"])
    def test_main_plot_positional_all(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="all", output=None, history_path=None
        )

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot", "--metric", "cpu"])
    def test_main_plot_flag_metric_backward_compatibility(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="cpu", output=None, history_path=None
        )

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot", "cpu", "--output", "/tmp/out.png"])
    def test_main_plot_positional_with_output(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="cpu", output="/tmp/out.png", history_path=None
        )

    @patch("sysbench.cli.run_plot")
    @patch("sys.argv", ["sysbench", "plot", "--history", "/tmp/custom.json"])
    def test_main_plot_with_history(self, mock_run_plot):
        mock_run_plot.return_value = [MagicMock()]
        main()
        mock_run_plot.assert_called_once_with(
            metric="all", output=None, history_path="/tmp/custom.json"
        )

    def test_main_plot_invalid_positional_metric(self):
        with patch("sys.argv", ["sysbench", "plot", "invalid_metric"]):
            with self.assertRaises(SystemExit):
                main()

    def test_main_plot_invalid_flag_metric(self):
        with patch("sys.argv", ["sysbench", "plot", "--metric", "invalid_metric"]):
            with self.assertRaises(SystemExit):
                main()


class TestCLIPlot(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_history = [
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
        ]
        self.history_file = Path(self.temp_dir.name) / "test_history.json"
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.mock_history, f)

    def tearDown(self):
        plt.close("all")
        self.temp_dir.cleanup()

    @patch("sysbench.cli.plot_cpu_usage")
    def test_run_plot_cpu_metric(self, mock_plot_cpu):
        mock_fig = MagicMock()
        mock_plot_cpu.return_value = mock_fig

        figs = run_plot(
            metric="cpu", history_path=self.history_file, show=False
        )

        self.assertEqual(figs, [mock_fig])
        mock_plot_cpu.assert_called_once_with(
            self.mock_history, output_path=None, show=False
        )

    @patch("sysbench.cli.plot_memory_usage")
    def test_run_plot_memory_metric(self, mock_plot_memory):
        mock_fig = MagicMock()
        mock_plot_memory.return_value = mock_fig

        figs = run_plot(
            metric="memory", history_path=self.history_file, show=False
        )

        self.assertEqual(figs, [mock_fig])
        mock_plot_memory.assert_called_once_with(
            self.mock_history, output_path=None, show=False
        )

    @patch("sysbench.cli.plot_latency")
    def test_run_plot_latency_metric(self, mock_plot_latency):
        mock_fig = MagicMock()
        mock_plot_latency.return_value = mock_fig

        figs = run_plot(
            metric="latency", history_path=self.history_file, show=False
        )

        self.assertEqual(figs, [mock_fig])
        mock_plot_latency.assert_called_once_with(
            self.mock_history, output_path=None, show=False
        )

    @patch("sysbench.cli.plot_latency")
    @patch("sysbench.cli.plot_memory_usage")
    @patch("sysbench.cli.plot_cpu_usage")
    def test_run_plot_all_metric(self, mock_cpu, mock_mem, mock_lat):
        mock_cpu.return_value = MagicMock()
        mock_mem.return_value = MagicMock()
        mock_lat.return_value = MagicMock()

        figs = run_plot(
            metric="all", history_path=self.history_file, show=False
        )

        self.assertIsNotNone(figs)
        assert figs is not None
        self.assertEqual(len(figs), 3)
        mock_cpu.assert_called_once_with(
            self.mock_history, output_path=None, show=False
        )
        mock_mem.assert_called_once_with(
            self.mock_history, output_path=None, show=False
        )
        mock_lat.assert_called_once_with(
            self.mock_history, output_path=None, show=False
        )

    @patch("sysbench.cli.plot_cpu_usage")
    def test_run_plot_custom_history_path(self, mock_plot_cpu):
        custom_data = [{"timestamp": "2026-10-01T12:00:00", "cpu_usage": 45.0}]
        custom_file = Path(self.temp_dir.name) / "custom.json"
        with open(custom_file, "w", encoding="utf-8") as f:
            json.dump(custom_data, f)

        run_plot(metric="cpu", history_path=custom_file, show=False)
        mock_plot_cpu.assert_called_once_with(
            custom_data, output_path=None, show=False
        )

    def test_run_plot_output_file_creation(self):
        output_file = Path(self.temp_dir.name) / "single_cpu.png"
        figs = run_plot(
            metric="cpu",
            output=output_file,
            history_path=self.history_file,
            show=False,
        )

        self.assertIsNotNone(figs)
        assert figs is not None
        self.assertEqual(len(figs), 1)
        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 0)

    def test_run_plot_deterministic_output_naming_for_all(self):
        base_output = Path(self.temp_dir.name) / "report.png"
        figs = run_plot(
            metric="all",
            output=base_output,
            history_path=self.history_file,
            show=False,
        )

        self.assertIsNotNone(figs)
        assert figs is not None
        self.assertEqual(len(figs), 3)

        # Base file should not be created directly
        self.assertFalse(base_output.exists())

        # Derived files must exist and be non-empty
        cpu_path = Path(self.temp_dir.name) / "report_cpu.png"
        mem_path = Path(self.temp_dir.name) / "report_memory.png"
        lat_path = Path(self.temp_dir.name) / "report_latency.png"

        self.assertTrue(cpu_path.exists())
        self.assertTrue(mem_path.exists())
        self.assertTrue(lat_path.exists())

        self.assertGreater(cpu_path.stat().st_size, 0)
        self.assertGreater(mem_path.stat().st_size, 0)
        self.assertGreater(lat_path.stat().st_size, 0)

    def test_run_plot_invalid_metric(self):
        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr):
            result = run_plot(
                metric="invalid_metric",
                history_path=self.history_file,
                show=False,
            )

        self.assertIsNone(result)
        self.assertIn("Invalid metric", captured_stderr.getvalue())

    def test_run_plot_missing_history_file(self):
        missing_path = Path(self.temp_dir.name) / "missing.json"
        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr):
            result = run_plot(
                metric="cpu", history_path=missing_path, show=False
            )

        self.assertIsNone(result)
        self.assertIn("History file not found", captured_stderr.getvalue())

    def test_run_plot_malformed_history_json(self):
        bad_json_file = Path(self.temp_dir.name) / "bad.json"
        with open(bad_json_file, "w", encoding="utf-8") as f:
            f.write("{unclosed_json:")

        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr):
            result = run_plot(
                metric="cpu", history_path=bad_json_file, show=False
            )

        self.assertIsNone(result)
        self.assertIn("contains invalid JSON", captured_stderr.getvalue())

    def test_run_plot_history_not_a_list(self):
        dict_json_file = Path(self.temp_dir.name) / "not_list.json"
        with open(dict_json_file, "w", encoding="utf-8") as f:
            f.write('{"timestamp": "2026-10-01", "cpu_usage": 10.0}')

        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr):
            result = run_plot(
                metric="cpu", history_path=dict_json_file, show=False
            )

        self.assertIsNone(result)
        self.assertIn(
            "must contain a JSON list of records", captured_stderr.getvalue()
        )

    def test_derive_metric_output_path(self):
        self.assertEqual(
            derive_metric_output_path("report.png", "cpu"),
            Path("report_cpu.png"),
        )
        self.assertEqual(
            derive_metric_output_path("/tmp/charts/sys.png", "memory"),
            Path("/tmp/charts/sys_memory.png"),
        )
        self.assertEqual(
            derive_metric_output_path("chart", "latency"),
            Path("chart_latency.png"),
        )

    def test_cli_help_documents_plot_command(self):
        parser = build_parser()
        help_text = parser.format_help()
        self.assertIn("plot", help_text)
        self.assertIn("check", help_text)
        self.assertIn("report", help_text)
        self.assertIn("monitor", help_text)
        self.assertIn("network", help_text)
        self.assertIn("--output", help_text)
        self.assertIn("--history", help_text)


if __name__ == "__main__":
    unittest.main()
