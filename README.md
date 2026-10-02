# SysBench

SysBench is a lightweight, CLI-first Linux system performance analyzer focused on collecting essential system metrics, validating them against configurable warning and failure thresholds, generating human-readable and structured reports, monitoring performance trends over time, and producing clean visualizations. Designed as a modular and installable Python utility, SysBench provides system administrators and developers with rapid, deterministic insights into CPU, memory, disk, system load, and network health without external infrastructure overhead.

---

## Features

- **CPU Usage Collection**: Measures multi-core CPU utilization percentage, logical core count, and system load average.
- **Memory Usage Collection**: Tracks virtual memory statistics including total, used, available memory, and percent utilization.
- **Disk Usage Collection**: Gathers storage metrics for the root filesystem, reporting total capacity, used space, free space, and usage percentage.
- **System Load Collection**: Captures 1-minute, 5-minute, and 15-minute system load averages, computing core-normalized load ratios.
- **Network Latency & Packet Loss**: Probes ICMP round-trip times (minimum, average, maximum RTT) and packet loss percentage against target hosts.
- **Network Interface Statistics**: Collects per-interface I/O metrics, including bytes transmitted/received, packets sent/received, packet drops, and transmission errors.
- **Configurable Thresholds**: Manages baseline warning and failure thresholds defined via bundled JSON configuration (`sysbench/config.json`).
- **Metric Validation**: Automatically evaluates collected metrics against threshold limits, assigning explicit `PASS`, `WARNING`, or `FAIL` ratings.
- **Overall Status Aggregation**: Synthesizes individual metric statuses into a single deterministic system status (`PASS`, `WARNING`, or `FAIL`).
- **Console Reports**: Renders clean, formatted ASCII tables suitable for terminal output and automated log inspection.
- **JSON Reports**: Emits structured, machine-parsable JSON performance snapshots including UTC timestamps and per-subsystem details.
- **Continuous Monitoring**: Executes periodic start-to-start sampling loops with monotonic interval compensation and graceful `Ctrl+C` handling.
- **Persistent Monitoring History**: Stores historical monitoring samples to standard XDG user state (`$XDG_STATE_HOME/sysbench/monitor_history.json` or `~/.local/state/sysbench/monitor_history.json`).
- **Performance Visualization**: Produces clean time-series plots for CPU usage, memory utilization, and network latency using Matplotlib with headless `Agg` backend support for file export.
- **Simplified CLI Interface**: Provides an intuitive command-line interface with positional arguments and backward-compatible option flags.
- **Modern Python Packaging**: Packages as a standard PEP 517/518 and PEP 621 compliant distribution providing the `sysbench` console script.
- **Automated Test Suite**: Verified by an automated unit test suite covering collectors, validation rules, reporting, visualization, CLI dispatch, and monitoring loops.

---

## Requirements

- **Operating System**: Linux
- **Python**: Version **3.12** or higher
- **Python Dependencies**:
  - `psutil>=5.9.0` (system metric collection)
  - `matplotlib>=3.7.0` (time-series visualization)
- **System Utilities**:
  - Host `ping` utility (`/bin/ping` or `iputils-ping`) for network latency and packet loss measurement.

> [!NOTE]
> Network latency and packet loss collection invokes the host operating system's `ping` command via subprocess execution and parses standard `iputils-ping` output.

---

## Installation

### Standard Installation

Clone the repository and install SysBench into an active virtual environment:

```bash
# Clone the repository and navigate into it
git clone <repository-url>
cd Sysbench

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install SysBench
pip install .
```

`pip install .` is the standard installation method. It installs the package and creates the `sysbench` executable in your environment's `bin/` directory.

### Developer Installation (Editable Mode)

When actively developing or modifying SysBench source code, install in editable mode:

```bash
pip install -e .
```

In editable mode, changes to the source files in `sysbench/` take effect immediately without requiring re-installation.

### Wheel Distribution Build (Packaging Workflow)

To build a standalone wheel distribution package:

```bash
# Build the wheel package into dist/
pip wheel --no-deps -w dist .

# Install the generated wheel
pip install dist/sysbench-0.1.0-py3-none-any.whl
```

---

## Quick Start

Once installed, run the primary SysBench commands directly from the terminal:

```bash
# 1. Run full system validation check with tabular ASCII output
sysbench check

# 2. Generate a structured JSON report
sysbench report

# 3. Inspect network latency and interface diagnostics
sysbench network

# 4. Start continuous performance monitoring (press Ctrl+C to stop)
sysbench monitor

# 5. Generate trend visualization plot file
sysbench plot cpu --output cpu_trend.png
```

---

## CLI Usage & Commands

```
usage: sysbench [-h] {check,report,monitor,network,plot} ...
```

### 1. `sysbench check`
Executes CPU, memory, disk, load, and network collectors, validates all readings against configured thresholds, and prints a comprehensive tabular ASCII report:

```bash
sysbench check
```

### 2. `sysbench report`
Gathers full system telemetry and outputs a structured JSON document to stdout, suitable for ingestion by log collectors or automation pipelines:

```bash
sysbench report
```

### 3. `sysbench network`
Performs network diagnostics by pinging the default probe target (`1.1.1.1`), analyzing latency statistics (min/avg/max), calculating packet loss, and displaying per-interface byte and error counters:

```bash
sysbench network
```

### 4. `sysbench monitor`
Launches a continuous monitoring loop that samples system state at regular intervals:

```bash
sysbench monitor
```

- **Sampling Interval**: Runs with an internal default interval of **5.0 seconds**. The loop calculates start-to-start elapsed time using `time.monotonic()` to compensate for metric collection duration. *(Note: The CLI runs with this fixed default interval; there is no `--interval` CLI option.)*
- **Graceful Shutdown**: Pressing `Ctrl+C` terminates monitoring cleanly without tracebacks, displaying total sample counts and destination path.
- **History Storage**: Samples are saved by default to the user state directory:
  - `$XDG_STATE_HOME/sysbench/monitor_history.json`
  - Fallback: `~/.local/state/sysbench/monitor_history.json`

### 5. `sysbench plot`
Renders time-series performance plots from monitoring history.

SysBench uses Matplotlib's non-interactive `Agg` backend (`FigureCanvasAgg`), which is specifically designed for reliable, headless file generation. Supplying the `--output` option saves the plot image directly to disk.

```bash
# Generate CPU usage plot and save to file
sysbench plot cpu --output cpu_trend.png

# Generate Memory usage plot and save to file
sysbench plot memory --output memory_trend.png

# Generate Network latency plot and save to file
sysbench plot latency --output latency_trend.png

# Generate all three plots with derived filenames
sysbench plot all --output system_report.png
# (Derives system_report_cpu.png, system_report_memory.png, system_report_latency.png)

# Read from a custom monitoring history file
sysbench plot latency --history /path/to/custom_history.json --output latency.png
```

**Plot Options:**
- `metric` *(positional, optional)*: Target metric to visualize (`cpu`, `memory`, `latency`, `all`). Default: `all`.
- `--output`, `-o` *(optional)*: Destination file path for the plot figure. Supplying `--output` ensures clean, headless file generation. *(Note: While `--output` is grammatically optional in the CLI, running without `--output` attempts interactive display via `plt.show()`, which raises a warning under the headless `Agg` backend.)*
- `--history` *(optional)*: Explicit path to a custom monitoring history JSON file to read instead of the default user state file.
- `--metric` *(optional flag)*: Supported for backward compatibility (e.g. `sysbench plot --metric cpu --output cpu.png`).

---

## Configuration

SysBench threshold limits are defined in [sysbench/config.json](sysbench/config.json), which is packaged as package data alongside the library.

### Default Thresholds

```json
{
  "cpu_usage": {
    "warning": 75,
    "fail": 90
  },
  "memory_usage": {
    "warning": 75,
    "fail": 90
  },
  "disk_usage": {
    "warning": 80,
    "fail": 95
  },
  "system_load": {
    "warning": 1.0,
    "fail": 1.5
  },
  "latency_ms": {
    "warning": 50,
    "fail": 100
  },
  "packet_loss_percent": {
    "warning": 1,
    "fail": 5
  }
}
```

### Validation Rules
- `PASS`: Metric value is strictly below the `warning` threshold.
- `WARNING`: Metric value meets or exceeds `warning`, but is strictly below `fail`.
- `FAIL`: Metric value meets or exceeds `fail`. For network latency, if the host ping fails to measure latency (returning `None`), latency evaluates to `FAIL`.
- `OVERALL STATUS`: Resolves to `FAIL` if any subsystem fails, `WARNING` if any subsystem has a warning (and none failed), or `PASS` if all metrics pass.

---

## Running Tests

SysBench uses Python's standard `unittest` framework with no extra testing dependencies required.

Run the test suite from the repository root:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

**Test Coverage Summary (115 tests, 0 failures, 0 errors):**
- `test_cli.py`: CLI parser arguments, subcommands, dispatch logic, and plot output handling.
- `test_config.py`: Threshold schema validation, error cases, and package config discovery.
- `test_core.py`: Orchestration of collectors and multi-metric validation aggregation.
- `test_monitor.py`: Start-to-start monotonic timing compensation, history persistence, XDG path resolution, and error recovery.
- `test_network.py`: Ping stdout/stderr parsing, RTT calculation, and interface metrics collection.
- `test_plot.py`: Data sanitization, empty history handling, headless figure creation, and file export.
- `test_reporting.py`: Console ASCII rendering and structured JSON report formatting.
- `test_validation.py`: Metric threshold boundary evaluation and overall status calculation.

---

## Project Structure

```
.
├── .gitignore
├── pyproject.toml
├── README.md
├── sysbench/
│   ├── cli.py
│   ├── config.json
│   ├── config.py
│   ├── core.py
│   ├── cpu.py
│   ├── disk.py
│   ├── load.py
│   ├── memory.py
│   ├── monitor.py
│   ├── network.py
│   ├── reporting/
│   │   ├── console.py
│   │   ├── __init__.py
│   │   ├── json_report.py
│   │   └── plot.py
│   └── validation/
│       ├── __init__.py
│       └── validator.py
├── tests/
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_core.py
│   ├── test_monitor.py
│   ├── test_network.py
│   ├── test_plot.py
│   ├── test_reporting.py
│   └── test_validation.py
```

---

## Known Limitations

- **Host `ping` Dependency**: Network latency and packet loss diagnostics execute the host's `/bin/ping` binary via subprocess. On minimal Linux containers or unprivileged environments lacking raw socket capabilities or the `ping` utility, latency metrics will report as unavailable (`FAIL`).
