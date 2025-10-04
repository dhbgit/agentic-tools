import subprocess
from datetime import datetime

class DiskHygieneAgent:
    def scan(self):
        timestamp = datetime.now().isoformat()
        df_output = self._run_df()
        du_output = self._run_du(depth=6, limit=100)

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

    def _run_du(self, depth=6, limit=100):
        try:
            cmd = f"du -h -d {depth} / | sort -hr | head -n {limit}"
            result = subprocess.check_output(cmd, shell=True, text=True)
            lines = result.strip().split("\n")
            return [
                {"size": line.split()[0], "path": line.split()[-1]}
                for line in lines if line.strip()
            ]
        except Exception as e:
            return [{"error": str(e)}]