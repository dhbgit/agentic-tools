from agents.scrape_asx_tickers import scrape_asx_tickers
from agents.rank_asx_tickers import rank_tickers_by_volume

def fetch_top_asx(limit=10):
    tickers = scrape_asx_tickers()
    top_tickers = rank_tickers_by_volume(tickers, limit=limit)
    return top_tickers