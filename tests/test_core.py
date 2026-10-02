import unittest
from unittest.mock import patch

from sysbench.core import collect_and_validate


class TestCore(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            "cpu_usage": {"warning": 75, "fail": 90},
            "memory_usage": {"warning": 75, "fail": 90},
            "disk_usage": {"warning": 80, "fail": 95},
            "system_load": {"warning": 1.0, "fail": 1.5},
            "latency_ms": {"warning": 50, "fail": 100},
            "packet_loss_percent": {"warning": 1, "fail": 5},
        }
        self.mock_cpu = {
            "usage_percent": 25.0,
            "core_count": 8,
            "load_average": 1.2,
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
            "load_1min": 1.5,
            "load_5min": 1.2,
            "load_15min": 1.0,
        }
        self.mock_network = {
            "latency_min_ms": 10.0,
            "latency_avg_ms": 15.0,
            "latency_max_ms": 20.0,
            "packet_loss_percent": 0.0,
            "interfaces": {
                "eth0": {
                    "bytes_sent": 1000,
                    "bytes_received": 2000,
                    "packets_sent": 10,
                    "packets_received": 20,
                    "errors": 0,
                    "drops": 0,
                }
            },
        }

    @patch("sysbench.core.get_ping_metrics")
    @patch("sysbench.core.get_load_metrics")
    @patch("sysbench.core.get_disk_metrics")
    @patch("sysbench.core.get_memory_metrics")
    @patch("sysbench.core.get_cpu_metrics")
    @patch("sysbench.core.validate_config")
    @patch("sysbench.core.load_config")
    def test_collect_and_validate_calls_collectors_and_returns_tuple(
        self,
        mock_load_config,
        mock_validate_config,
        mock_get_cpu,
        mock_get_mem,
        mock_get_disk,
        mock_get_load,
        mock_get_net,
    ):
        mock_load_config.return_value = self.mock_config
        mock_validate_config.return_value = True
        mock_get_cpu.return_value = self.mock_cpu
        mock_get_mem.return_value = self.mock_memory
        mock_get_disk.return_value = self.mock_disk
        mock_get_load.return_value = self.mock_load
        mock_get_net.return_value = self.mock_network

        result = collect_and_validate()

        # Verify config loaded and validated
        mock_load_config.assert_called_once()
        mock_validate_config.assert_called_once_with(self.mock_config)

        # Verify collectors were called
        mock_get_cpu.assert_called_once()
        mock_get_mem.assert_called_once()
        mock_get_disk.assert_called_once()
        mock_get_load.assert_called_once()
        mock_get_net.assert_called_once()

        # Verify return structure: 7 elements
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 7)

        cpu, memory, disk, load, network, statuses, overall_status = result

        self.assertEqual(cpu, self.mock_cpu)
        self.assertEqual(memory, self.mock_memory)
        self.assertEqual(disk, self.mock_disk)
        self.assertEqual(load, self.mock_load)
        self.assertEqual(network, self.mock_network)

        # 6 individual statuses: cpu, mem, disk, load, latency, packet_loss
        self.assertEqual(len(statuses), 6)
        self.assertEqual(statuses, ["PASS", "PASS", "PASS", "PASS", "PASS", "PASS"])
        self.assertEqual(overall_status, "PASS")

    @patch("sysbench.core.get_ping_metrics")
    @patch("sysbench.core.get_load_metrics")
    @patch("sysbench.core.get_disk_metrics")
    @patch("sysbench.core.get_memory_metrics")
    @patch("sysbench.core.get_cpu_metrics")
    @patch("sysbench.core.validate_config")
    @patch("sysbench.core.load_config")
    def test_collect_and_validate_overall_status_warning(
        self,
        mock_load_config,
        mock_validate_config,
        mock_get_cpu,
        mock_get_mem,
        mock_get_disk,
        mock_get_load,
        mock_get_net,
    ):
        mock_load_config.return_value = self.mock_config
        mock_validate_config.return_value = True
        # Set CPU usage into WARNING range (>= 75, < 90)
        cpu_warning = dict(self.mock_cpu, usage_percent=80.0)
        mock_get_cpu.return_value = cpu_warning
        mock_get_mem.return_value = self.mock_memory
        mock_get_disk.return_value = self.mock_disk
        mock_get_load.return_value = self.mock_load
        mock_get_net.return_value = self.mock_network

        result = collect_and_validate()
        statuses = result[5]
        overall_status = result[6]

        self.assertEqual(statuses[0], "WARNING")
        self.assertEqual(overall_status, "WARNING")

    @patch("sysbench.core.get_ping_metrics")
    @patch("sysbench.core.get_load_metrics")
    @patch("sysbench.core.get_disk_metrics")
    @patch("sysbench.core.get_memory_metrics")
    @patch("sysbench.core.get_cpu_metrics")
    @patch("sysbench.core.validate_config")
    @patch("sysbench.core.load_config")
    def test_collect_and_validate_overall_status_fail(
        self,
        mock_load_config,
        mock_validate_config,
        mock_get_cpu,
        mock_get_mem,
        mock_get_disk,
        mock_get_load,
        mock_get_net,
    ):
        mock_load_config.return_value = self.mock_config
        mock_validate_config.return_value = True
        mock_get_cpu.return_value = self.mock_cpu
        mock_get_mem.return_value = self.mock_memory
        mock_get_disk.return_value = self.mock_disk
        mock_get_load.return_value = self.mock_load
        # Set packet loss into FAIL range (>= 5%)
        net_fail = dict(self.mock_network, packet_loss_percent=10.0)
        mock_get_net.return_value = net_fail

        result = collect_and_validate()
        statuses = result[5]
        overall_status = result[6]

        self.assertEqual(statuses[5], "FAIL")
        self.assertEqual(overall_status, "FAIL")


if __name__ == "__main__":
    unittest.main()
