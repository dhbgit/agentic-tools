import subprocess
from datetime import datetime  # ✅ fixed

class DiskHygieneAgent:
    def scan(self):
        timestamp = datetime.now().isoformat()
        df_output = self._run_df()
        du_output = self._run_du()

        return {
            "timestamp": timestamp,
            "df": df_output,
            "du": du_output
        }

    def _run_df(self):
        try:
            result = subprocess.check_output(["df", "-h"], text=True)
            return result.strip()
        except Exception as e:
            return f"Error running df: {e}"

    def _run_du(self):
        try:
            result = subprocess.check_output(
                "du -h ~ | sort -hr | head -n 20",
                shell=True,
                text=True
            )
            return result.strip().split("\n")
        except Exception as e:
            return [f"Error running du: {e}"]