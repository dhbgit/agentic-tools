from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

def log_info(message: str) -> None:
    """
    Simple compatibility wrapper used by agents that just need
    to record a plain text event in the workspace log.
    """
    try:
        log_entry(message=message)
    except Exception:
        # Fall back to stdout so the agent still reports progress
        print(message)


DEFAULT_LOG_DIR = Path(
    os.environ.get(
        "AGENTIC_LOG_DIR",
        str(Path.home() / "repos" / "agentic_tools" / "workspace_logger"),
    )
).expanduser()

LOG_FILE = Path(
    os.environ.get("AGENTIC_LOG_FILE", DEFAULT_LOG_DIR / "workspace_log.txt")
).expanduser()

MILESTONE_FILE = Path(
    os.environ.get("AGENTIC_MILESTONE_FILE", DEFAULT_LOG_DIR / "milestones.txt")
).expanduser()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_line(path: Path, line: str) -> None:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def log_entry(
    mode: str,
    note: str = "",
    *,
    timestamp: Optional[str] = None,
    path: Optional[Union[str, Path]] = None,
    echo: bool = True,
) -> str:
    entry_time = timestamp or datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    line = f"[{entry_time}] Mode: {mode}"
    if note:
        line += f" | Note: {note}"

    target_path = Path(path).expanduser() if path else LOG_FILE
    _write_line(target_path, line)

    if echo:
        print(f"[log_entry] {line}")

    return line


def log_milestone(
    mode: Union[str, Dict[str, Any], None] = None,
    note: Optional[str] = None,
    reflection: Optional[str] = None,
    *,
    timestamp: Optional[str] = None,
    path: Optional[Union[str, Path]] = None,
    echo: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if isinstance(mode, dict):
        entry = mode.copy()
        entry.setdefault("mode", "OTHER")
        entry.setdefault("note", "")
        entry.setdefault("reflection", "")
        entry.setdefault("timestamp", timestamp or datetime.now().isoformat())
        if note is not None:
            entry["note"] = note
        if reflection is not None:
            entry["reflection"] = reflection
    else:
        mode_value = mode or "FLOW"
        note_value = note or ""
        reflection_value = reflection or ""

        entry = {
            "timestamp": timestamp or datetime.now().isoformat(),
            "mode": mode_value,
            "note": note_value,
            "reflection": reflection_value,
        }

    if extra:
        existing_extra = entry.get("extra")
        if isinstance(existing_extra, dict):
            existing_extra.update(extra)
        else:
            entry["extra"] = extra

    line = _format_milestone_line(entry)

    target_path = Path(path).expanduser() if path else MILESTONE_FILE
    _write_line(target_path, line)

    if echo:
        print(f"[milestone] {line}")

    return entry


def log_reflection(
    reflection: str,
    note: str = "",
    *,
    mode: str = "REFLECT",
    **kwargs: Any,
) -> Dict[str, Any]:
    return log_milestone(
        mode=mode,
        note=note,
        reflection=reflection,
        **kwargs,
    )


def log_flow(note: str, reflection: str = "", **kwargs: Any) -> Dict[str, Any]:
    return log_milestone(
        mode="FLOW",
        note=note,
        reflection=reflection,
        **kwargs,
    )


def log_fix(note: str, reflection: str = "", **kwargs: Any) -> Dict[str, Any]:
    return log_milestone(
        mode="FIX",
        note=note,
        reflection=reflection,
        **kwargs,
    )


def log_plan(note: str, reflection: str = "", **kwargs: Any) -> Dict[str, Any]:
    return log_milestone(
        mode="PLAN",
        note=note,
        reflection=reflection,
        **kwargs,
    )


def _format_milestone_line(entry: Dict[str, Any]) -> str:
    base = f"[{entry['timestamp']}] Mode: {entry['mode']} | Note: {entry['note']}"
    reflection = entry.get("reflection")
    if reflection:
        base += f" | Reflection: {reflection}"

    extra = entry.get("extra")
    if isinstance(extra, dict) and extra:
        fragments = [f"{key}={value}" for key, value in sorted(extra.items())]
        base += " | Extra: " + ", ".join(fragments)

    return base


def interactive_milestone() -> None:
    print("\nMilestone Logger – Interactive Mode")
    print("Select mode:")
    print("  1. PLAN\n  2. VALIDATE\n  3. FLOW\n  4. FIX\n  5. OTHER")

    choices = {
        "1": "PLAN",
        "2": "VALIDATE",
        "3": "FLOW",
        "4": "FIX",
        "5": "OTHER",
    }

    mode = choices.get(input("Enter choice (1-5): ").strip(), "OTHER")
    note = input("Milestone note:\n> ").strip()
    reflection = input("Reflection:\n> ").strip()

    log_milestone(mode=mode, note=note, reflection=reflection)


if __name__ == "__main__":
    interactive_milestone()
