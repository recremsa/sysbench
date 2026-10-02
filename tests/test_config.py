import unittest
from unittest.mock import mock_open, patch
import json

from sysbench.config import load_config, validate_config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.valid_config = {
            "cpu_usage": {"warning": 75, "fail": 90},
            "memory_usage": {"warning": 75, "fail": 90},
            "disk_usage": {"warning": 80, "fail": 95},
            "system_load": {"warning": 1.0, "fail": 1.5},
            "latency_ms": {"warning": 50, "fail": 100},
            "packet_loss_percent": {"warning": 1, "fail": 5},
        }

    def test_load_config_valid(self):
        config_data = json.dumps(self.valid_config)
        with patch("builtins.open", mock_open(read_data=config_data)):
            loaded = load_config()
            self.assertEqual(loaded, self.valid_config)

    def test_validate_config_valid(self):
        result = validate_config(self.valid_config)
        self.assertTrue(result)

    def test_validate_config_missing_required_section(self):
        required = [
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "latency_ms",
            "packet_loss_percent",
        ]
        for section in required:
            cfg = dict(self.valid_config)
            del cfg[section]
            with self.assertRaises(ValueError) as ctx:
                validate_config(cfg)
            self.assertIn(f"Missing configuration section: {section}", str(ctx.exception))

    def test_validate_config_missing_warning_threshold(self):
        cfg = json.loads(json.dumps(self.valid_config))
        del cfg["cpu_usage"]["warning"]
        with self.assertRaises(ValueError) as ctx:
            validate_config(cfg)
        self.assertIn("Missing thresholds in: cpu_usage", str(ctx.exception))

    def test_validate_config_missing_fail_threshold(self):
        cfg = json.loads(json.dumps(self.valid_config))
        del cfg["memory_usage"]["fail"]
        with self.assertRaises(ValueError) as ctx:
            validate_config(cfg)
        self.assertIn("Missing thresholds in: memory_usage", str(ctx.exception))

    def test_validate_config_non_numeric_warning(self):
        cfg = json.loads(json.dumps(self.valid_config))
        cfg["disk_usage"]["warning"] = "eighty"
        with self.assertRaises(ValueError) as ctx:
            validate_config(cfg)
        self.assertIn("Warning threshold must be numeric: disk_usage", str(ctx.exception))

    def test_validate_config_non_numeric_fail(self):
        cfg = json.loads(json.dumps(self.valid_config))
        cfg["latency_ms"]["fail"] = None
        with self.assertRaises(ValueError) as ctx:
            validate_config(cfg)
        self.assertIn("Fail threshold must be numeric: latency_ms", str(ctx.exception))

    def test_validate_config_warning_greater_than_fail(self):
        cfg = json.loads(json.dumps(self.valid_config))
        cfg["cpu_usage"]["warning"] = 95
        cfg["cpu_usage"]["fail"] = 90
        with self.assertRaises(ValueError) as ctx:
            validate_config(cfg)
        self.assertIn("Warning threshold must be lower than fail: cpu_usage", str(ctx.exception))

    def test_validate_config_warning_equal_to_fail(self):
        cfg = json.loads(json.dumps(self.valid_config))
        cfg["cpu_usage"]["warning"] = 90
        cfg["cpu_usage"]["fail"] = 90
        with self.assertRaises(ValueError) as ctx:
            validate_config(cfg)
        self.assertIn("Warning threshold must be lower than fail: cpu_usage", str(ctx.exception))

    def test_validate_config_system_load_covered(self):
        """Test that system_load section is validated.
        
        Exposes production bug: sysbench/config.py:validate_config() omits
        'system_load' from required_sections, so missing system_load is not
        rejected.
        """
        cfg = json.loads(json.dumps(self.valid_config))
        del cfg["system_load"]
        with self.assertRaises(ValueError) as ctx:
            validate_config(cfg)
        self.assertIn("system_load", str(ctx.exception))

    def test_default_config_path_exists_and_valid(self):
        from sysbench.config import CONFIG_PATH
        self.assertTrue(CONFIG_PATH.is_file(), f"CONFIG_PATH does not exist: {CONFIG_PATH}")
        config = load_config()
        self.assertTrue(validate_config(config))


if __name__ == "__main__":
    unittest.main()
