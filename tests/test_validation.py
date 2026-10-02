import unittest

from sysbench.validation.validator import (
    get_overall_status,
    validate_cpu,
    validate_disk,
    validate_latency,
    validate_memory,
    validate_metric,
    validate_packet_loss,
    validate_system_load,
)


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.config = {
            "cpu_usage": {"warning": 75, "fail": 90},
            "memory_usage": {"warning": 75, "fail": 90},
            "disk_usage": {"warning": 80, "fail": 95},
            "system_load": {"warning": 1.0, "fail": 1.5},
            "latency_ms": {"warning": 50, "fail": 100},
            "packet_loss_percent": {"warning": 1, "fail": 5},
        }

    # validate_metric tests
    def test_validate_metric_pass(self):
        self.assertEqual(validate_metric(40, 75, 90), "PASS")
        self.assertEqual(validate_metric(74.9, 75, 90), "PASS")

    def test_validate_metric_warning(self):
        self.assertEqual(validate_metric(75, 75, 90), "WARNING")
        self.assertEqual(validate_metric(80, 75, 90), "WARNING")
        self.assertEqual(validate_metric(89.9, 75, 90), "WARNING")

    def test_validate_metric_fail(self):
        self.assertEqual(validate_metric(90, 75, 90), "FAIL")
        self.assertEqual(validate_metric(95, 75, 90), "FAIL")

    # validate_cpu tests
    def test_validate_cpu_pass(self):
        self.assertEqual(validate_cpu({"usage_percent": 30.0}, self.config), "PASS")

    def test_validate_cpu_warning(self):
        self.assertEqual(validate_cpu({"usage_percent": 75.0}, self.config), "WARNING")

    def test_validate_cpu_fail(self):
        self.assertEqual(validate_cpu({"usage_percent": 92.5}, self.config), "FAIL")

    # validate_memory tests
    def test_validate_memory_pass(self):
        self.assertEqual(validate_memory({"usage_percent": 50.0}, self.config), "PASS")

    def test_validate_memory_warning(self):
        self.assertEqual(validate_memory({"usage_percent": 78.0}, self.config), "WARNING")

    def test_validate_memory_fail(self):
        self.assertEqual(validate_memory({"usage_percent": 91.0}, self.config), "FAIL")

    # validate_disk tests
    def test_validate_disk_pass(self):
        self.assertEqual(validate_disk({"usage_percent": 40.0}, self.config), "PASS")

    def test_validate_disk_warning(self):
        self.assertEqual(validate_disk({"usage_percent": 82.0}, self.config), "WARNING")

    def test_validate_disk_fail(self):
        self.assertEqual(validate_disk({"usage_percent": 96.0}, self.config), "FAIL")

    # validate_system_load tests
    def test_validate_system_load_pass(self):
        # 4 cores, load 2.0 -> ratio 0.5 < 1.0 (PASS)
        cpu_metrics = {"core_count": 4}
        load_metrics = {"load_1min": 2.0}
        self.assertEqual(validate_system_load(load_metrics, cpu_metrics, self.config), "PASS")

    def test_validate_system_load_warning(self):
        # 4 cores, load 4.8 -> ratio 1.2 (>= 1.0, < 1.5 -> WARNING)
        cpu_metrics = {"core_count": 4}
        load_metrics = {"load_1min": 4.8}
        self.assertEqual(validate_system_load(load_metrics, cpu_metrics, self.config), "WARNING")

    def test_validate_system_load_fail(self):
        # 4 cores, load 6.5 -> ratio 1.625 (>= 1.5 -> FAIL)
        cpu_metrics = {"core_count": 4}
        load_metrics = {"load_1min": 6.5}
        self.assertEqual(validate_system_load(load_metrics, cpu_metrics, self.config), "FAIL")

    # validate_latency tests
    def test_validate_latency_pass(self):
        self.assertEqual(validate_latency({"latency_avg_ms": 25.0}, self.config), "PASS")

    def test_validate_latency_warning(self):
        self.assertEqual(validate_latency({"latency_avg_ms": 65.0}, self.config), "WARNING")

    def test_validate_latency_fail(self):
        self.assertEqual(validate_latency({"latency_avg_ms": 110.0}, self.config), "FAIL")

    def test_validate_latency_none_returns_fail(self):
        # When ping receives no response, latency_avg_ms is None
        self.assertEqual(validate_latency({"latency_avg_ms": None}, self.config), "FAIL")

    # validate_packet_loss tests
    def test_validate_packet_loss_pass(self):
        self.assertEqual(validate_packet_loss({"packet_loss_percent": 0.0}, self.config), "PASS")

    def test_validate_packet_loss_warning(self):
        self.assertEqual(validate_packet_loss({"packet_loss_percent": 2.5}, self.config), "WARNING")

    def test_validate_packet_loss_fail(self):
        self.assertEqual(validate_packet_loss({"packet_loss_percent": 10.0}, self.config), "FAIL")

    # get_overall_status tests
    def test_get_overall_status_all_pass(self):
        statuses = ["PASS", "PASS", "PASS", "PASS", "PASS", "PASS"]
        self.assertEqual(get_overall_status(statuses), "PASS")

    def test_get_overall_status_one_warning(self):
        statuses = ["PASS", "WARNING", "PASS", "PASS", "PASS", "PASS"]
        self.assertEqual(get_overall_status(statuses), "WARNING")

    def test_get_overall_status_one_fail(self):
        statuses = ["PASS", "PASS", "PASS", "FAIL", "PASS", "PASS"]
        self.assertEqual(get_overall_status(statuses), "FAIL")

    def test_get_overall_status_multiple_warning_no_fail(self):
        statuses = ["WARNING", "PASS", "WARNING", "PASS", "WARNING", "PASS"]
        self.assertEqual(get_overall_status(statuses), "WARNING")

    def test_get_overall_status_multiple_fail_and_warning(self):
        statuses = ["WARNING", "FAIL", "PASS", "FAIL", "WARNING", "PASS"]
        self.assertEqual(get_overall_status(statuses), "FAIL")

    def test_get_overall_status_empty_list(self):
        self.assertEqual(get_overall_status([]), "PASS")


if __name__ == "__main__":
    unittest.main()
