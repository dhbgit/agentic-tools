from datetime import date
from pathlib import Path
import subprocess
from agentic_tools.workspace_logger.logger import log_info

class StockAnalysisAgent:
    """
    Agent that triggers the agentic_stock_system_starter backtest pipeline.
    """

    def __init__(self, tickers=None, start="2018-01-01"):
        self.tickers = tickers or ["AAPL", "MSFT", "NVDA"]
        self.start = start
        # project root relative path
        self.project_dir = Path(__file__).resolve().parents[3] / "agentic_stock_system_starter"

    def run(self):
        log_info(f"[{date.today()}] ▶️ StockAnalysisAgent starting for {self.tickers}")
        cmd = [
            "python", "-m", "src.backtest",
            "--tickers", *self.tickers,
            "--start", self.start,
        ]
        try:
            subprocess.run(cmd, cwd=self.project_dir, check=True)
            log_info("✅ StockAnalysisAgent completed successfully.")
        except Exception as e:
            log_info(f"❌ StockAnalysisAgent failed: {e}")