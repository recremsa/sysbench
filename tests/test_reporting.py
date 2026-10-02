import io
import json
import unittest
from unittest.mock import patch

from sysbench.reporting.console import print_report
from sysbench.reporting.json_report import generate_json_report, print_json_report


class TestReporting(unittest.TestCase):
    def setUp(self):
        self.mock_cpu = {
            "usage_percent": 35.5,
            "core_count": 4,
            "load_average": 1.1,
        }
        self.mock_memory = {
            "total": 16000000000,
            "used": 8000000000,
            "available": 8000000000,
            "usage_percent": 50.0,
        }
        self.mock_disk = {
            "total": 500000000000,
            "used": 100000000000,
            "available": 400000000000,
            "usage_percent": 20.0,
        }
        self.mock_load = {
            "load_1min": 1.12,
            "load_5min": 1.05,
            "load_15min": 0.95,
        }
        self.mock_network = {
            "latency_min_ms": 12.3,
            "latency_avg_ms": 15.4,
            "latency_max_ms": 20.1,
            "packet_loss_percent": 0.0,
            "interfaces": {
                "eth0": {
                    "bytes_sent": 500000,
                    "bytes_received": 1200000,
                    "packets_sent": 300,
                    "packets_received": 700,
                    "errors": 0,
                    "drops": 0,
                },
                "wlan0": {
                    "bytes_sent": 10000,
                    "bytes_received": 25000,
                    "packets_sent": 50,
                    "packets_received": 80,
                    "errors": 1,
                    "drops": 2,
                },
            },
        }
        self.mock_statuses = [
            "PASS",  # cpu
            "PASS",  # memory
            "PASS",  # disk
            "PASS",  # load
            "PASS",  # latency
            "PASS",  # packet loss
        ]
        self.mock_overall_status = "PASS"

    def test_console_report_renders_valid_output(self):
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_report(
                self.mock_cpu,
                self.mock_memory,
                self.mock_disk,
                self.mock_load,
                self.mock_network,
                self.mock_statuses,
                self.mock_overall_status,
            )

        output = captured_output.getvalue()

        # Check headers and sections
        self.assertIn("SYSBENCH REPORT", output)
        self.assertIn("SYSTEM", output)
        self.assertIn("NETWORK", output)
        self.assertIn("INTERFACE", output)

        # Check metric values and statuses
        self.assertIn("CPU Usage", output)
        self.assertIn("35.5%", output)
        self.assertIn("Memory Usage", output)
        self.assertIn("50.0%", output)
        self.assertIn("Disk Usage", output)
        self.assertIn("20.0%", output)
        self.assertIn("System Load", output)
        self.assertIn("1.12", output)
        self.assertIn("Latency", output)
        self.assertIn("15.4 ms", output)
        self.assertIn("Packet Loss", output)
        self.assertIn("0.0%", output)

        # Check interfaces rendered
        self.assertIn("Interface              eth0", output)
        self.assertIn("Interface              wlan0", output)
        self.assertIn("RX                     1200000 bytes", output)
        self.assertIn("TX                     500000 bytes", output)

        # Check overall status badge
        self.assertIn("SYSTEM STATUS: PASS", output)

    def test_generate_json_report_structure_and_fields(self):
        report = generate_json_report(
            self.mock_cpu,
            self.mock_memory,
            self.mock_disk,
            self.mock_load,
            self.mock_network,
            self.mock_statuses,
            self.mock_overall_status,
        )

        self.assertIsInstance(report, dict)

        # Top-level required fields
        self.assertIn("timestamp", report)
        self.assertIn("cpu", report)
        self.assertIn("memory", report)
        self.assertIn("disk", report)
        self.assertIn("system_load", report)
        self.assertIn("network", report)
        self.assertIn("interfaces", report)
        self.assertIn("status", report)

        # Value and status fields within blocks
        self.assertEqual(report["cpu"]["usage_percent"], 35.5)
        self.assertEqual(report["cpu"]["status"], "PASS")

        self.assertEqual(report["memory"]["usage_percent"], 50.0)
        self.assertEqual(report["memory"]["status"], "PASS")

        self.assertEqual(report["disk"]["usage_percent"], 20.0)
        self.assertEqual(report["disk"]["status"], "PASS")

        self.assertEqual(report["system_load"]["load_1min"], 1.12)
        self.assertEqual(report["system_load"]["status"], "PASS")

        self.assertEqual(report["network"]["latency_min_ms"], 12.3)
        self.assertEqual(report["network"]["latency_avg_ms"], 15.4)
        self.assertEqual(report["network"]["latency_max_ms"], 20.1)
        self.assertEqual(report["network"]["packet_loss_percent"], 0.0)
        self.assertEqual(report["network"]["latency_status"], "PASS")
        self.assertEqual(report["network"]["packet_loss_status"], "PASS")

        self.assertEqual(report["status"], "PASS")
        self.assertIn("eth0", report["interfaces"])
        self.assertIn("wlan0", report["interfaces"])

    def test_print_json_report_outputs_valid_json(self):
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_json_report(
                self.mock_cpu,
                self.mock_memory,
                self.mock_disk,
                self.mock_load,
                self.mock_network,
                self.mock_statuses,
                self.mock_overall_status,
            )

        output = captured_output.getvalue()
        # Verify output is valid JSON
        parsed = json.loads(output)
        self.assertEqual(parsed["status"], "PASS")
        self.assertEqual(parsed["cpu"]["usage_percent"], 35.5)

    def test_print_network_report_with_none_latency(self):
        from sysbench.reporting.console import print_network_report

        net_no_rtt = dict(self.mock_network, latency_min_ms=None, latency_avg_ms=None, latency_max_ms=None, packet_loss_percent=100.0)
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_network_report(net_no_rtt, "FAIL", "FAIL", "FAIL")

        output = captured_output.getvalue()
        self.assertIn("SYSBENCH NETWORK REPORT", output)
        self.assertIn("Latency Avg            N/A       FAIL", output)
        self.assertIn("Packet Loss            100.0%       FAIL", output)
        self.assertIn("NETWORK STATUS: FAIL", output)


if __name__ == "__main__":
    unittest.main()
