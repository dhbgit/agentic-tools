import os
import subprocess
from datetime import datetime
from agentic_tools.utils.path_utils import get_repo_root
repo_root = get_repo_root()
from agentic_tools.workspace_logger.logger import log_milestone
import agentic_tools.workspace_logger.logger as logger
print(f"[logger module] using: {logger.__file__}")

# 🧠 RECOMMENDATION: Replace raw string with structured milestone dict
log_milestone({
    "timestamp": datetime.now().isoformat(),
    "mode": "FLOW",
    "note": "Disk hygiene agent reached",
    "reflection": "Agent entrypoint confirmed via orchestrator"
})

# 🧠 RECOMMENDATION: Confirm execution context for debugging
print(f"[cwd] {os.getcwd()}")
print(f"[logger path] {os.path.join(os.path.dirname(__file__), 'milestones.txt')}")

class DiskHygieneAgent:
    def scan(self, depth=None, limit=None):
        timestamp = datetime.now().isoformat()

        # 🧠 RECOMMENDATION: Log scan start milestone
        log_milestone({
            "timestamp": timestamp,
            "mode": "FLOW",
            "note": f"Disk hygiene scan started at {timestamp}",
            "reflection": f"Parameters: depth={depth or 'default'}, limit={limit or 'default'}"
        })

        df_output = self._run_df()
        log_milestone({
            "timestamp": timestamp,
            "mode": "FLOW",
            "note": "df output preview",
            "reflection": "\n".join(df_output.splitlines()[:5])  # first 5 lines
        })
        du_output = self._run_du(depth=depth, limit=limit)
        self.reflect_on_du(du_output)

        report = {
            "timestamp": timestamp,
            "df": df_output,
            "du": du_output
        }

        # 🧠 RECOMMENDATION: Log scan completion milestone
        log_milestone({
            "timestamp": timestamp,
            "mode": "REFLECT",
            "note": "Disk hygiene summary",
            "reflection": f"Scan completed. du returned {len(du_output)} entries. df captured {len(df_output.splitlines())} lines."
        })

        self.write_summary(report)
        return report

    def _run_df(self):
        try:
            result = subprocess.check_output(["df", "-h"], text=True)
            return result.strip()
        except Exception as e:
            # 🧠 RECOMMENDATION: Log failure as milestone
            log_milestone({
                "timestamp": datetime.now().isoformat(),
                "mode": "ERROR",
                "note": "df command failed",
                "reflection": str(e)
            })
            return f"Error running df: {e}"

    def _run_du(self, depth=None, limit=None):
        try:
            depth = depth if depth is not None else 6
            limit = limit if limit is not None else 100
            cmd = f"du -h -d {depth} / | sort -hr | head -n {limit}"
            result = subprocess.check_output(cmd, shell=True, text=True)
            lines = result.strip().split("\n")
            return [
                {"size": line.split()[0], "path": line.split()[-1]}
                for line in lines if line.strip()
            ]
        except Exception as e:
            # 🧠 RECOMMENDATION: Log failure as milestone
            log_milestone({
                "timestamp": datetime.now().isoformat(),
                "mode": "ERROR",
                "note": "du command failed",
                "reflection": str(e)
            })
            return [{"error": str(e)}]

    def write_summary(self, report, path=None):
        path = path or os.path.expanduser("~/repos/agentic_tools/workspace_logger/workspace_log.txt")
        try:
            with open(path, "a") as f:
                f.write(f"\n[SUMMARY] {report['timestamp']}\n")
                f.write("Disk Usage (df):\n")
                f.write(report["df"] + "\n\n")
                f.write("Top Directories (du):\n")
                for entry in report["du"]:
                    f.write(f"{entry.get('size', '?')}  {entry.get('path', '?')}\n")
        except Exception as e:
            # 🧠 RECOMMENDATION: Log write failure
            log_milestone({
                "timestamp": datetime.now().isoformat(),
                "mode": "ERROR",
                "note": "Failed to write summary",
                "reflection": str(e)
            })

    def reflect_on_du(self, du_output):
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
    
            def summarize(entries, label):
                large = [e for e in entries if e.get("size", "").endswith("G") or e.get("size", "").endswith("M")]
                top = large[:3]
                return f"{label}: " + ", ".join([f"{e['size']} → {e['path']}" for e in top])
    
            reflection = "\n".join([
                summarize(categories["user"], "User data"),
                summarize(categories["apps"], "Applications"),
                summarize(categories["system"], "System files")
            ])
    
            log_milestone({
                "timestamp": datetime.now().isoformat(),
                "mode": "REFLECT",
                "note": "Disk hygiene interpretation",
                "reflection": reflection
            })
    
        except Exception as e:
            log_milestone({
                "timestamp": datetime.now().isoformat(),
                "mode": "ERROR",
                "note": "Reflection on du output failed",
                "reflection": str(e)
            })            
if __name__ == "__main__":
    agent = DiskHygieneAgent()
    result = agent.scan()
    print(f"[agent result] keys: {list(result.keys())}")