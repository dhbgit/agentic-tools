import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from agentic_tools.workspace_logger.logger import log_milestone, log_reflection
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    from workspace_logger.logger import log_milestone, log_reflection


class DiskHygieneAgent:
    def __init__(
        self,
        scan_roots: Optional[Iterable[Path]] = None,
        safe_cleanup_roots: Optional[Iterable[Path]] = None,
        default_depth: int = 3,
        default_limit: int = 50,
        min_cleanup_bytes: int = 200 * 1024 * 1024,
    ):
        self.home = Path.home()
        self.default_depth = default_depth
        self.default_limit = default_limit
        self.min_cleanup_bytes = min_cleanup_bytes

        self.scan_roots = self._resolve_scan_roots(scan_roots)
        self.safe_cleanup_roots = self._resolve_safe_roots(safe_cleanup_roots)

    def scan(
        self,
        depth: Optional[int] = None,
        limit: Optional[int] = None,
        auto_cleanup: bool = True,
        roots: Optional[Iterable[Path]] = None,
    ):
        timestamp = datetime.now().isoformat()
        depth = depth if depth is not None else self.default_depth
        limit = limit if limit is not None else self.default_limit
        roots_to_scan = self._resolve_scan_roots(roots) if roots is not None else self.scan_roots

        log_milestone(
            "FLOW",
            note="Disk hygiene scan started",
            reflection=f"depth={depth}, limit={limit}, roots={[str(r) for r in roots_to_scan]}",
            timestamp=timestamp,
        )

        df_output = self._run_df()
        preview_lines = "\n".join(df_output.splitlines()[:5]) if df_output else "df command returned no output"
        log_milestone(
            "FLOW",
            note="df output preview",
            reflection=preview_lines,
            timestamp=timestamp,
        )

        du_entries = self._run_du(roots_to_scan, depth=depth, limit=limit)
        self.reflect_on_du(du_entries)

        cleanup_actions: List[dict] = []
        if auto_cleanup:
            cleanup_actions = self.cleanup_safe_targets(du_entries)

        report = {
            "timestamp": timestamp,
            "df": df_output,
            "du": du_entries,
            "scan_roots": [str(path) for path in roots_to_scan],
            "cleanup_actions": cleanup_actions,
        }

        log_milestone(
            "REFLECT",
            note="Disk hygiene summary",
            reflection=(
                f"Scan complete: {len(du_entries)} du entries, "
                f"{len(cleanup_actions)} cleanup actions."
            ),
            timestamp=timestamp,
        )

        self.write_summary(report)
        return report

    def _run_df(self) -> str:
        try:
            result = subprocess.run(
                ["df", "-h"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            if result.stderr:
                log_milestone(
                    "OBSERVE",
                    note="df stderr",
                    reflection=result.stderr.strip(),
                )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "df command failed")
            return result.stdout.strip()
        except Exception as exc:
            log_milestone(
                "ERROR",
                note="df command failed",
                reflection=str(exc),
            )
            return f"Error running df: {exc}"

    def _run_du(self, roots: List[Path], depth: int, limit: int) -> List[dict]:
        if not roots:
            log_milestone(
                "OBSERVE",
                note="No scan roots",
                reflection="Skipping du; no directories available to inspect.",
            )
            return []

        entries: List[dict] = []
        for root in roots:
            entries.extend(self._run_du_for_root(root, depth))

        entries.sort(key=lambda item: item.get("size_bytes", 0), reverse=True)
        return entries[:limit]

    def _run_du_for_root(self, root: Path, depth: int) -> List[dict]:
        if not root.exists():
            return []

        command = ["du", "-k", "-x", "-d", str(depth), str(root)]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
        except subprocess.TimeoutExpired:
            log_milestone(
                "ERROR",
                note="du command timed out",
                reflection=f"Root={root}, depth={depth}",
            )
            return []

        if result.stderr:
            log_milestone(
                "OBSERVE",
                note=f"du stderr for {root}",
                reflection=result.stderr.strip(),
            )

        lines = result.stdout.splitlines()
        entries: List[dict] = []

        for raw_line in lines:
            parts = raw_line.strip().split("\t", 1)
            if len(parts) != 2:
                parts = raw_line.strip().split(maxsplit=1)
            if len(parts) != 2:
                continue

            size_str, path_str = parts
            try:
                size_kb = int(size_str)
            except ValueError:
                continue

            entries.append({
                "size_bytes": size_kb * 1024,
                "size": self._format_size(size_kb * 1024),
                "path": path_str,
                "root": str(root),
            })

        return entries

    def cleanup_safe_targets(self, du_entries: List[dict]) -> List[dict]:
        actions: List[dict] = []
        if not self.safe_cleanup_roots:
            return actions

        processed: set[str] = set()
        for entry in du_entries:
            path_str = entry.get("path")
            size_bytes = entry.get("size_bytes")
            if not path_str:
                continue

            candidate_path = self._normalize_path(path_str)
            normalized_str = str(candidate_path)
            if normalized_str in processed or not candidate_path.exists():
                continue

            safe_root = self._match_safe_root(candidate_path)
            if safe_root is None:
                continue

            if size_bytes is not None:
                try:
                    size_bytes = int(size_bytes)
                except (TypeError, ValueError):
                    size_bytes = None

            if size_bytes is None:
                size_bytes = self._compute_path_size(candidate_path)

            if not self._is_removal_allowed(candidate_path):
                log_milestone(
                    "OBSERVE",
                    note=f"Skipped {normalized_str}",
                    reflection="Path is protected or lacks delete permissions.",
                )
                continue

            if size_bytes < self.min_cleanup_bytes and safe_root.name != ".Trash":
                continue

            try:
                if candidate_path == safe_root:
                    freed_bytes = self._clear_directory_contents(candidate_path)
                else:
                    freed_bytes = self._remove_path(candidate_path)
            except PermissionError as exc:
                log_milestone(
                    "OBSERVE",
                    note=f"Skipped {normalized_str}",
                    reflection=f"Permission denied: {exc}",
                )
                continue
            except Exception as exc:
                log_milestone(
                    "ERROR",
                    note=f"Failed to prune {candidate_path}",
                    reflection=str(exc),
                )
                continue

            freed_bytes = freed_bytes or size_bytes or 0
            if freed_bytes <= 0:
                continue

            processed.add(normalized_str)
            action = {
                "path": normalized_str,
                "bytes_freed": freed_bytes,
                "human_freed": self._format_size(freed_bytes),
                "safe_root": str(safe_root),
            }
            actions.append(action)

            log_milestone(
                "FIX",
                note=f"Auto-cleaned {normalized_str}",
                reflection=f"Freed approximately {action['human_freed']} (under {safe_root})",
            )

        return actions

    def write_summary(self, report: dict, path: Optional[str] = None) -> None:
        log_path = Path(path or "~/repos/agentic_tools/workspace_logger/workspace_log.txt").expanduser()

        try:
            with open(log_path, "a") as handle:
                handle.write(f"\n[SUMMARY] {report['timestamp']}\n")
                handle.write("Scanned Roots:\n")
                for root in report.get("scan_roots", []):
                    handle.write(f"- {root}\n")
                handle.write("\nDisk Usage (df):\n")
                handle.write((report.get("df") or "Unavailable") + "\n\n")
                handle.write("Top Directories (du):\n")
                for entry in report.get("du", []):
                    handle.write(f"{entry.get('size', '?')}  {entry.get('path', '?')}\n")
                cleanup_actions = report.get("cleanup_actions", [])
                handle.write("\nCleanup Actions:\n")
                if cleanup_actions:
                    for action in cleanup_actions:
                        handle.write(
                            f"- Freed {action.get('human_freed', '?')} from {action.get('path', '?')}"
                            f" (safe root: {action.get('safe_root', '?')})\n"
                        )
                else:
                    handle.write("- None\n")
        except Exception as exc:
            log_milestone(
                "ERROR",
                note="Failed to write summary",
                reflection=str(exc),
            )

    def reflect_on_du(self, du_output: List[dict]) -> None:
        try:
            categories = {
                "user": [],
                "apps": [],
                "system": [],
                "other": []
            }

            for entry in du_output:
                path = entry.get("path", "")
                size = entry.get("size", "?")

                if path.startswith("/Users") or path.startswith("/Library") or path.startswith("/Pictures"):
                    categories["user"].append(entry)
                elif "/Applications" in path or "Code.app" in path or "Spotify.app" in path:
                    categories["apps"].append(entry)
                elif path.startswith("/System") or path.startswith("/private"):
                    categories["system"].append(entry)
                else:
                    categories["other"].append(entry)

            def summarize(entries: List[dict], label: str) -> str:
                large = [e for e in entries if isinstance(e.get("size"), str) and (e["size"].endswith("G") or e["size"].endswith("M"))]
                top = large[:3]
                return f"{label}: " + ", ".join([f"{e['size']} → {e['path']}" for e in top]) if top else f"{label}: none"

            reflection = "\n".join([
                summarize(categories["user"], "User data"),
                summarize(categories["apps"], "Applications"),
                summarize(categories["system"], "System files")
            ])

            log_reflection(
                reflection,
                note="Disk hygiene interpretation",
            )

        except Exception as exc:
            log_milestone(
                "ERROR",
                note="Reflection on du output failed",
                reflection=str(exc),
            )

    def _clear_directory_contents(self, directory: Path) -> int:
        total = 0
        if not directory.exists() or not directory.is_dir():
            return total

        for child in directory.iterdir():
            try:
                total += self._remove_path(child)
            except PermissionError as exc:
                log_milestone(
                    "OBSERVE",
                    note=f"Skipped {child}",
                    reflection=f"Permission denied: {exc}",
                )
            except Exception as exc:
                log_milestone(
                    "ERROR",
                    note=f"Failed to remove {child}",
                    reflection=str(exc),
                )

        return total

    def _remove_path(self, path: Path) -> int:
        if not self._is_removal_allowed(path):
            raise PermissionError("Removal not allowed for protected path.")

        size = self._compute_path_size(path)

        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path)

        return size

    def _compute_path_size(self, path: Path) -> int:
        try:
            if path.is_symlink():
                return path.lstat().st_size
            if path.is_file():
                return path.stat().st_size
            if not path.is_dir():
                return 0
        except OSError:
            return 0

        total = 0

        def _ignore(_: OSError) -> None:
            return None

        for root, _, files in os.walk(path, onerror=_ignore):
            root_path = Path(root)
            for name in files:
                file_path = root_path / name
                try:
                    if file_path.is_symlink():
                        total += file_path.lstat().st_size
                    else:
                        total += file_path.stat().st_size
                except OSError:
                    continue

        return total

    def _match_safe_root(self, path: Path) -> Optional[Path]:
        for safe_root in self.safe_cleanup_roots:
            try:
                path.relative_to(safe_root)
                return safe_root
            except ValueError:
                continue

        return None

    def _is_removal_allowed(self, path: Path) -> bool:
        if not path.exists():
            return False

        if any(part.startswith("com.apple") for part in path.parts):
            return False

        try:
            target = path if path.is_file() else path.resolve()
        except OSError:
            target = path

        parent = target.parent if target.parent != target else None

        checks: List[bool] = []
        try:
            if target.is_dir():
                checks.append(os.access(target, os.W_OK | os.X_OK))
            else:
                checks.append(os.access(target, os.W_OK))
        except OSError:
            checks.append(False)

        if parent is not None:
            try:
                checks.append(os.access(parent, os.W_OK | os.X_OK))
            except OSError:
                checks.append(False)

        return all(checks) and path != Path.home()

    def _resolve_scan_roots(self, roots: Optional[Iterable[Path]]) -> List[Path]:
        if roots is None:
            return self._default_scan_roots()

        resolved = [self._normalize_path(path) for path in roots]
        return [path for path in resolved if path.exists()]

    def _resolve_safe_roots(self, roots: Optional[Iterable[Path]]) -> List[Path]:
        if roots is None:
            return self._default_safe_roots()

        resolved = [self._normalize_path(path) for path in roots]
        return [path for path in resolved if path.exists()]

    def _default_scan_roots(self) -> List[Path]:
        candidates = [
            self.home / "Downloads",
            self.home / "Documents",
            self.home / "Desktop",
            self.home / "Library" / "Caches",
            self.home / "Library" / "Logs",
            self.home / "Library" / "Developer" / "Xcode" / "DerivedData",
            self.home / "repos",
        ]
        return [path for path in candidates if path.exists()]

    def _default_safe_roots(self) -> List[Path]:
        candidates = [
            self.home / "Library" / "Caches",
            self.home / "Library" / "Logs",
            self.home / "Library" / "Developer" / "Xcode" / "DerivedData",
            self.home / ".Trash",
        ]
        return [path for path in candidates if path.exists()]

    def _normalize_path(self, candidate: Path) -> Path:
        try:
            expanded = Path(candidate).expanduser()
        except Exception:
            expanded = Path(str(candidate))

        try:
            return expanded.resolve(strict=False)
        except Exception:
            return expanded

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes is None or size_bytes < 0:
            return "?"

        units = ["B", "K", "M", "G", "T", "P"]
        value = float(size_bytes)

        for unit in units:
            if value < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(value)}B"
                if value >= 10:
                    return f"{value:.0f}{unit}"
                return f"{value:.1f}{unit}"
            value /= 1024

        return f"{value:.1f}P"


def check_disk_usage(depth: Optional[int] = None, limit: Optional[int] = None):
    agent = DiskHygieneAgent()
    return agent.scan(depth=depth, limit=limit)


if __name__ == "__main__":
    agent = DiskHygieneAgent()
    result = agent.scan()
    print(f"[agent result] keys: {list(result.keys())}")
