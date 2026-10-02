from collections import namedtuple
import subprocess
import unittest
from unittest.mock import patch

from sysbench.network import get_interface_metrics, get_ping_metrics


# Create namedtuple matching psutil snetio structure
NetIOCounters = namedtuple(
    "snetio",
    [
        "bytes_sent",
        "bytes_recv",
        "packets_sent",
        "packets_recv",
        "errin",
        "errout",
        "dropin",
        "dropout",
    ],
)


class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.mock_interfaces = {
            "eth0": {
                "bytes_sent": 1000,
                "bytes_received": 2000,
                "packets_sent": 10,
                "packets_received": 20,
                "errors": 0,
                "drops": 0,
            }
        }

    @patch("sysbench.network.psutil.net_io_counters")
    def test_get_interface_metrics(self, mock_net_io):
        mock_net_io.return_value = {
            "eth0": NetIOCounters(
                bytes_sent=1048576,
                bytes_recv=2097152,
                packets_sent=1500,
                packets_recv=2500,
                errin=1,
                errout=2,
                dropin=3,
                dropout=4,
            ),
            "lo": NetIOCounters(
                bytes_sent=5000,
                bytes_recv=5000,
                packets_sent=50,
                packets_recv=50,
                errin=0,
                errout=0,
                dropin=0,
                dropout=0,
            ),
        }

        result = get_interface_metrics()

        self.assertIn("eth0", result)
        self.assertIn("lo", result)

        eth0 = result["eth0"]
        self.assertEqual(eth0["bytes_sent"], 1048576)
        self.assertEqual(eth0["bytes_received"], 2097152)
        self.assertEqual(eth0["packets_sent"], 1500)
        self.assertEqual(eth0["packets_received"], 2500)
        self.assertEqual(eth0["errors"], 3)  # errin(1) + errout(2)
        self.assertEqual(eth0["drops"], 7)   # dropin(3) + dropout(4)

        lo = result["lo"]
        self.assertEqual(lo["errors"], 0)
        self.assertEqual(lo["drops"], 0)

    @patch("sysbench.network.get_interface_metrics")
    @patch("sysbench.network.subprocess.run")
    def test_get_ping_metrics_successful(self, mock_run, mock_get_interfaces):
        mock_get_interfaces.return_value = self.mock_interfaces
        ping_stdout = (
            "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n"
            "64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=14.2 ms\n"
            "64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=15.1 ms\n"
            "64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=16.8 ms\n"
            "64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=14.9 ms\n"
            "\n"
            "--- 1.1.1.1 ping statistics ---\n"
            "4 packets transmitted, 4 received, 0.0% packet loss, time 3004ms\n"
            "rtt min/avg/max/mdev = 14.200/15.250/16.800/0.950 ms\n"
        )
        mock_run.return_value = subprocess.CompletedProcess(
            args=["ping", "-c", "4", "1.1.1.1"],
            returncode=0,
            stdout=ping_stdout,
            stderr="",
        )

        result = get_ping_metrics(host="1.1.1.1", count=4)

        mock_run.assert_called_once_with(
            ["ping", "-c", "4", "1.1.1.1"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result["latency_min_ms"], 14.2)
        self.assertEqual(result["latency_avg_ms"], 15.25)
        self.assertEqual(result["latency_max_ms"], 16.8)
        self.assertEqual(result["packet_loss_percent"], 0.0)
        self.assertEqual(result["interfaces"], self.mock_interfaces)

    @patch("sysbench.network.get_interface_metrics")
    @patch("sysbench.network.subprocess.run")
    def test_get_ping_metrics_with_packet_loss(self, mock_run, mock_get_interfaces):
        mock_get_interfaces.return_value = self.mock_interfaces
        ping_stdout = (
            "--- 1.1.1.1 ping statistics ---\n"
            "4 packets transmitted, 2 received, 50.0% packet loss, time 3012ms\n"
            "rtt min/avg/max/mdev = 15.000/18.000/21.000/3.000 ms\n"
        )
        mock_run.return_value = subprocess.CompletedProcess(
            args=["ping", "-c", "4", "1.1.1.1"],
            returncode=0,
            stdout=ping_stdout,
            stderr="",
        )

        result = get_ping_metrics(host="1.1.1.1", count=4)

        self.assertEqual(result["packet_loss_percent"], 50.0)
        self.assertEqual(result["latency_min_ms"], 15.0)
        self.assertEqual(result["latency_avg_ms"], 18.0)
        self.assertEqual(result["latency_max_ms"], 21.0)

    @patch("sysbench.network.get_interface_metrics")
    @patch("sysbench.network.subprocess.run")
    def test_get_ping_metrics_missing_rtt(self, mock_run, mock_get_interfaces):
        mock_get_interfaces.return_value = self.mock_interfaces
        ping_stdout = (
            "--- 1.1.1.1 ping statistics ---\n"
            "4 packets transmitted, 0 received, 100.0% packet loss, time 3060ms\n"
        )
        mock_run.return_value = subprocess.CompletedProcess(
            args=["ping", "-c", "4", "1.1.1.1"],
            returncode=1,
            stdout=ping_stdout,
            stderr="",
        )

        result = get_ping_metrics(host="1.1.1.1", count=4)

        self.assertEqual(result["packet_loss_percent"], 100.0)
        self.assertIsNone(result["latency_min_ms"])
        self.assertIsNone(result["latency_avg_ms"])
        self.assertIsNone(result["latency_max_ms"])
        self.assertEqual(result["interfaces"], self.mock_interfaces)

    @patch("sysbench.network.get_interface_metrics")
    @patch("sysbench.network.subprocess.run")
    def test_get_ping_metrics_malformed_output_raises_runtime_error(
        self, mock_run, mock_get_interfaces
    ):
        mock_get_interfaces.return_value = self.mock_interfaces
        mock_run.return_value = subprocess.CompletedProcess(
            args=["ping", "-c", "4", "1.1.1.1"],
            returncode=2,
            stdout="",
            stderr="ping: unknown host invalid.domain\n",
        )

        with self.assertRaises(RuntimeError) as ctx:
            get_ping_metrics(host="invalid.domain", count=4)

        self.assertIn("Unable to parse packet loss from ping output", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
