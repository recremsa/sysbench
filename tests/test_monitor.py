import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sysbench.monitor import (
    create_monitoring_record,
    format_sample_summary,
    get_default_history_path,
    load_monitoring_history,
    resolve_history_path,
    run_monitor,
    save_monitoring_history,
)


class TestMonitor(unittest.TestCase):
    def setUp(self):
        self.mock_results = (
            {"usage_percent": 35.5, "core_count": 8, "load_average": 1.2},
            {"total": 16000, "used": 8000, "available": 8000, "usage_percent": 50.0},
            {"total": 100000, "used": 20000, "available": 80000, "usage_percent": 20.0},
            {"load_1min": 1.5, "load_5min": 1.2, "load_15min": 1.0},
            {
                "latency_min_ms": 30.0,
                "latency_avg_ms": 42.5,
                "latency_max_ms": 55.0,
                "packet_loss_percent": 0.0,
                "interfaces": {},
            },
            ["PASS", "PASS", "PASS", "PASS", "PASS", "PASS"],
            "PASS",
        )

    def test_create_monitoring_record(self):
        record = create_monitoring_record(self.mock_results)
        self.assertIn("timestamp", record)
        self.assertEqual(record["cpu_usage"], 35.5)
        self.assertEqual(record["memory_usage"], 50.0)
        self.assertEqual(record["disk_usage"], 20.0)
        self.assertEqual(record["load_average"], 1.5)
        self.assertEqual(record["latency_ms"], 42.5)
        self.assertEqual(record["packet_loss"], 0.0)
        self.assertEqual(record["status"], "PASS")

    def test_format_sample_summary(self):
        summary = format_sample_summary(self.mock_results)
        self.assertIn("CPU: 35.5%", summary)
        self.assertIn("Memory: 50.0%", summary)
        self.assertIn("Disk: 20.0%", summary)
        self.assertIn("Load: 1.50", summary)
        self.assertIn("Latency: 42.5 ms", summary)
        self.assertIn("Loss: 0.0%", summary)
        self.assertIn("Status: PASS", summary)

    def test_format_sample_summary_with_none_values(self):
        none_results = (
            {"usage_percent": None},
            {"usage_percent": None},
            {"usage_percent": None},
            {"load_1min": None},
            {"latency_avg_ms": None, "packet_loss_percent": None},
            [],
            "FAIL",
        )
        summary = format_sample_summary(none_results)
        self.assertIn("CPU: N/A", summary)
        self.assertIn("Latency: N/A", summary)
        self.assertIn("Status: FAIL", summary)

    def test_resolve_history_path_explicit(self):
        explicit = Path("/custom/history.json")
        resolved = resolve_history_path(explicit)
        self.assertEqual(resolved, explicit)

    def test_get_default_history_path_uses_cwd_if_exists(self):
        with patch.object(Path, "is_file", return_value=True):
            path = get_default_history_path()
            self.assertEqual(path, Path("monitor_history.json"))

    def test_get_default_history_path_xdg_state(self):
        with patch.object(Path, "is_file", return_value=False):
            with patch.dict("os.environ", {"XDG_STATE_HOME": "/tmp/test_state"}):
                path = get_default_history_path()
                self.assertEqual(path, Path("/tmp/test_state/sysbench/monitor_history.json"))

    def test_load_monitoring_history_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "does_not_exist.json"
            history = load_monitoring_history(target)
            self.assertEqual(history, [])

    def test_load_monitoring_history_valid(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "history.json"
            sample_data = [{"timestamp": "2026-10-02T10:00:00Z", "cpu_usage": 10.0}]
            target.write_text(json.dumps(sample_data), encoding="utf-8")

            history = load_monitoring_history(target)
            self.assertEqual(history, sample_data)

    def test_load_monitoring_history_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "history.json"
            target.write_text("{ not valid json }", encoding="utf-8")

            history = load_monitoring_history(target)
            self.assertEqual(history, [])

    def test_load_monitoring_history_not_a_list(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "history.json"
            target.write_text(json.dumps({"key": "value"}), encoding="utf-8")

            history = load_monitoring_history(target)
            self.assertEqual(history, [])

    def test_save_monitoring_history_success_and_dir_creation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "nested" / "dir" / "history.json"
            sample_data = [{"timestamp": "2026-10-02T10:00:00Z", "cpu_usage": 10.0}]

            saved = save_monitoring_history(sample_data, target)
            self.assertTrue(saved)
            self.assertTrue(target.is_file())

            loaded = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(loaded, sample_data)

    def test_save_monitoring_history_permission_error(self):
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            saved = save_monitoring_history([], "/restricted/history.json")
            self.assertFalse(saved)

    @patch("sysbench.monitor.time.sleep")
    @patch("sysbench.monitor.time.monotonic")
    @patch("sysbench.monitor.collect_and_validate")
    def test_run_monitor_timing_interval_compensation(
        self, mock_collect, mock_monotonic, mock_sleep
    ):
        mock_collect.return_value = self.mock_results
        # Simulate:
        # loop 0 start: 100.0, elapsed: 1.2s -> next monotonic: 101.2
        # interval: 5.0 -> sleep should be 5.0 - 1.2 = 3.8s
        # loop 1 start: 105.0
        mock_monotonic.side_effect = [100.0, 101.2, 105.0, 106.0]

        with tempfile.TemporaryDirectory() as tmp_dir:
            history_file = Path(tmp_dir) / "history.json"
            history = run_monitor(
                interval=5.0,
                history_path=history_file,
                max_iterations=2,
            )
            self.assertEqual(len(history), 2)
            # Sleep was called with remaining duration ~ 3.8s
            mock_sleep.assert_called_once()
            slept = mock_sleep.call_args[0][0]
            self.assertAlmostEqual(slept, 3.8, places=2)

    @patch("sysbench.monitor.time.sleep")
    @patch("sysbench.monitor.time.monotonic")
    @patch("sysbench.monitor.collect_and_validate")
    def test_run_monitor_zero_remaining_sleep_when_elapsed_exceeds_interval(
        self, mock_collect, mock_monotonic, mock_sleep
    ):
        mock_collect.return_value = self.mock_results
        # Collection takes 6.0 seconds for a 5.0 second interval
        mock_monotonic.side_effect = [100.0, 106.0, 107.0, 108.0]

        with tempfile.TemporaryDirectory() as tmp_dir:
            history_file = Path(tmp_dir) / "history.json"
            history = run_monitor(
                interval=5.0,
                history_path=history_file,
                max_iterations=2,
            )
            self.assertEqual(len(history), 2)
            mock_sleep.assert_called_once_with(0.0)

    @patch("sysbench.monitor.collect_and_validate")
    def test_run_monitor_transient_collection_error_does_not_abort(
        self, mock_collect
    ):
        # 1st call fails, 2nd call succeeds
        mock_collect.side_effect = [RuntimeError("Ping failed"), self.mock_results]

        with patch("sysbench.monitor.time.sleep"):
            with tempfile.TemporaryDirectory() as tmp_dir:
                history_file = Path(tmp_dir) / "history.json"
                history = run_monitor(
                    interval=1.0,
                    history_path=history_file,
                    max_iterations=2,
                )
                # 1 successful record saved
                self.assertEqual(len(history), 1)

    @patch("sysbench.monitor.collect_and_validate")
    def test_run_monitor_keyboard_interrupt_handles_cleanly(self, mock_collect):
        mock_collect.side_effect = KeyboardInterrupt

        with tempfile.TemporaryDirectory() as tmp_dir:
            history_file = Path(tmp_dir) / "history.json"
            history = run_monitor(
                interval=1.0,
                history_path=history_file,
            )
            self.assertEqual(len(history), 0)
            self.assertTrue(history_file.is_file())

    def test_multiple_monitoring_sessions_append_history(self):
        with patch("sysbench.monitor.collect_and_validate", return_value=self.mock_results):
            with patch("sysbench.monitor.time.sleep"):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    history_file = Path(tmp_dir) / "history.json"

                    # Session 1
                    session1 = run_monitor(
                        interval=1.0,
                        history_path=history_file,
                        max_iterations=2,
                    )
                    self.assertEqual(len(session1), 2)

                    # Session 2
                    session2 = run_monitor(
                        interval=1.0,
                        history_path=history_file,
                        max_iterations=1,
                    )
                    self.assertEqual(len(session2), 3)

                    # Verify persisted on disk
                    persisted = json.loads(history_file.read_text(encoding="utf-8"))
                    self.assertEqual(len(persisted), 3)


if __name__ == "__main__":
    unittest.main()
