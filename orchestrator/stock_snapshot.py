import requests
from datetime import datetime
from agentic_tools.workspace_logger.logger import log_milestone

import os

API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
if not API_KEY:
    log_milestone(
        mode="ERROR",
        note="Missing Alpha Vantage API key",
        reflection="Set ALPHAVANTAGE_API_KEY in environment or config"
    )
    exit()

def fetch_stock_data(ticker):
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        quote = data.get("Global Quote", {})
        if not quote or "05. price" not in quote:
            log_milestone(
                mode="ERROR",
                note=f"Invalid response for {ticker}",
                reflection=f"Response: {data}"
            )
            return {"error": "Invalid response or ticker"}
        return {
            "symbol": quote.get("01. symbol", ticker),
            "price": quote["05. price"],
            "change": quote.get("09. change", "0"),
            "percent": quote.get("10. change percent", "0%")
        }
    except Exception as e:
        log_milestone(
            mode="ERROR",
            note=f"Failed to fetch stock data for {ticker}",
            reflection=str(e)
        )
        return {"error": str(e)}

def log_stock_snapshot(snapshot, metadata=None):
    if "error" in snapshot:
        print("Error:", snapshot["error"])
        return

    price = float(snapshot["price"])
    change = float(snapshot["change"])
    percent = snapshot["percent"]
    symbol = snapshot["symbol"]

    movement = "up" if change > 0 else "down" if change < 0 else "unchanged"
    reflection = f"Stock moved {movement} by {change} ({percent})"

    print(f"\n📈 {symbol} is {movement}")
    print(f"Price: ${price:.2f}")
    print(f"Change: {change:.2f} ({percent})\n")

    log_milestone(
        mode="FLOW",
        note=f"{symbol} snapshot: ${price:.2f}, change {change:.2f} ({percent})",
        reflection=reflection,
        **(metadata or {})
    )



if __name__ == "__main__":
    ticker = input("Enter stock ticker: ").strip().upper()
    snapshot = fetch_stock_data(ticker)
    log_stock_snapshot(snapshot)