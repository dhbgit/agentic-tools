from datetime import datetime
import sys
import os

# Path to your log file
LOG_FILE = os.path.expanduser("~/repos/agentic-tools/workspace_logger/workspace_log.txt")
MILESTONE_FILE = os.path.expanduser("~/repos/agentic-tools/workspace_logger/milestones.txt")

def log_entry(mode: str, note: str = ""):
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    entry = f"[{timestamp}] Mode: {mode}"
    if note:
        entry += f" | Note: {note}"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")
    print(f"Logged: {entry}")

def log_milestone(entry: dict):
    required_keys = ["timestamp", "mode", "note", "reflection"]
    for key in required_keys:
        if key not in entry:
            raise ValueError(f"Missing required log field: {key}")

    log_line = (
        f"[{entry['timestamp']}] Mode: {entry['mode']} | "
        f"Note: {entry['note']} | Reflection: {entry['reflection']}\n"
    )

    print(f"\n🪵 Milestone Logged:\n{log_line}")

    with open(MILESTONE_FILE, "a") as f:
        f.write(log_line)

# Fluid CLI input: python3 workspace_logger.py flow "Finished Alpha Vantage agent"
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 workspace_logger.py <mode> [note]")
        sys.exit(1)

    mode = sys.argv[1]
    note = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    log_entry(mode, note)