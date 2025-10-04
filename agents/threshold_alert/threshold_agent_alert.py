import yaml
import subprocess
from agentic_tools.workspace_logger.logger import log_milestone
import os
from agentic_tools.utils.path_utils import get_repo_root
repo_root = get_repo_root()

def load_thresholds():
    """Loads thresholds from config/thresholds.yaml if it exists and is valid."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, 'config', 'thresholds.yaml')

    if not os.path.exists(path):
        log_milestone(
            mode="ERROR",
            note="thresholds.yaml not found",
            reflection="Agent skipped threshold check; no config available"
        )
        return {}

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                log_milestone(
                    mode="ERROR",
                    note="thresholds.yaml has unexpected structure",
                    reflection="Expected {path: limit}, got something else"
                )
                return {}
            return data
    except Exception as e:
        log_milestone(
            mode="ERROR",
            note="Failed to load thresholds.yaml",
            reflection=str(e)
        )
        return {}
    
def get_disk_usage(path):
    """Returns disk usage in GB for the given path."""
    try:
        result = subprocess.run(
            ['du', '-sh', path],
            capture_output=True,
            text=True,
            check=True,
            timeout=30  # seconds
        )
        size_str = result.stdout.split()[0]
        return parse_size(size_str)
    except subprocess.TimeoutExpired:
        log_milestone(
            mode="ERROR",
            note=f"Timeout while checking usage for {path}",
            reflection="Scan exceeded 30s; consider narrowing scope or increasing timeout"
        )
        return 0
    except Exception as e:
        log_milestone(
            mode="ERROR",
            note=f"Failed to get disk usage for {path}",
            reflection=str(e)
        )
        return 0

def parse_size(size_str, units=None):
    """Parses size strings like '3.2G' or '512M' into GB."""
    units = units or {'K': 1/1024/1024, 'M': 1/1024, 'G': 1, 'T': 1024}
    try:
        num = float(size_str[:-1])
        unit = size_str[-1]
        return num * units.get(unit, 0)
    except Exception:
        return 0

def check_thresholds():
    thresholds = load_thresholds()
    if not thresholds:
        log_milestone(
            mode="FLOW",
            note="No thresholds to check",
            reflection="Agent ran but found no actionable config"
        )
        return

    for entry in thresholds.items() if isinstance(thresholds, dict) else enumerate(thresholds):
        path, limit_gb = None, None

        if isinstance(entry, tuple) and len(entry) == 2:
            path, limit_gb = entry
        elif isinstance(entry, dict) and "path" in entry and "limit" in entry:
            path, limit_gb = entry["path"], entry["limit"]
        else:
            log_milestone(
                mode="FLOW",
                note=f"Skipped malformed threshold entry: {entry}",
                reflection="Entry did not match expected structure"
            )
            continue

        usage_gb = get_disk_usage(path)
        if usage_gb > limit_gb:
            log_milestone(
                mode="ALERT",
                note=f"{path} exceeded threshold: {usage_gb:.2f}G > {limit_gb}G",
                reflection="Consider cleanup or archiving"
            )
        else:
            log_milestone(
                mode="FLOW",
                note=f"{path} within threshold: {usage_gb:.2f}G ≤ {limit_gb}G",
                reflection="No action needed"
            )

if __name__ == "__main__":
    check_thresholds()