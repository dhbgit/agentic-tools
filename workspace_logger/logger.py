from datetime import datetime
import os

LOG_FILE = os.path.expanduser("~/repos/agentic_tools/workspace_logger/workspace_log.txt")
MILESTONE_FILE = os.path.expanduser("~/repos/agentic_tools/workspace_logger/milestones.txt")

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

    # ✅ Confirm path and permissions
    print(f"[log_milestone] writing to: {MILESTONE_FILE}")
    try:
        with open(MILESTONE_FILE, "a") as f:
            f.write(log_line)
        print("🪵 Milestone Logged:")
        print(log_line)
    except Exception as e:
        print(f"[log_milestone] failed to write: {e}")

def interactive_milestone():
    print("\n🪪 Milestone Logger – Interactive Mode")

    # Mode selection
    print("Select mode:")
    print("  1. PLAN")
    print("  2. VALIDATE")
    print("  3. FLOW")
    print("  4. FIX")
    print("  5. OTHER")
    mode_map = {
        "1": "PLAN",
        "2": "VALIDATE",
        "3": "FLOW",
        "4": "FIX",
        "5": "OTHER"
    }
    mode_choice = input("Enter choice (1–5): ").strip()
    mode = mode_map.get(mode_choice, "OTHER")

    # Note and reflection
    note = input("What was the milestone note?\n> ").strip()
    reflection = input("What’s your reflection on this milestone?\n> ").strip()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "note": note,
        "reflection": reflection
    }

    log_milestone(entry)

if __name__ == "__main__":
    interactive_milestone()