import requests
from datetime import datetime
from agentic_tools.workspace_logger.logger import log_milestone

API_KEY = "DHQ425H8K37CBY7H"  # replace with your actual key
BASE_URL = "https://www.alphavantage.co/query"

def fetch_stock_data(ticker):
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    try:
        quote = data["Global Quote"]
        return {
            "symbol": quote["01. symbol"],
            "price": quote["05. price"],
            "change": quote["09. change"],
            "percent": quote["10. change percent"]
        }
    except KeyError:
        return {"error": "Invalid response or ticker"}

def log_stock_snapshot(snapshot):
    if "error" in snapshot:
        print("Error:", snapshot["error"])
        return

    price = float(snapshot["price"])
    change = float(snapshot["change"])
    percent = snapshot["percent"]

    # Basic analysis
    movement = "up" if change > 0 else "down" if change < 0 else "unchanged"
    reflection = f"Stock moved {movement} by {change} ({percent})"

    print(f"\n📈 {snapshot['symbol']} is {movement}")
    print(f"Price: ${price:.2f}")
    print(f"Change: {change:.2f} ({percent})\n")

    log_milestone({
        "timestamp": datetime.now().isoformat(),
        "mode": "FLOW",
        "note": f"{snapshot['symbol']} snapshot: ${price:.2f}, change {change:.2f} ({percent})",
        "reflection": reflection
    })



if __name__ == "__main__":
    ticker = input("Enter stock ticker: ").strip().upper()
    snapshot = fetch_stock_data(ticker)
    log_stock_snapshot(snapshot)