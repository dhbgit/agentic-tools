import yfinance as yf

def rank_tickers_by_volume(tickers, limit=10):
    ranked = []

    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="1d")
            if data.empty:
                continue

            volume = data['Volume'].iloc[-1]
            ranked.append((ticker, volume))
        except Exception:
            continue

    ranked.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in ranked[:limit]]