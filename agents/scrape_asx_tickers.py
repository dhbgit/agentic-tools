import requests
from bs4 import BeautifulSoup

def scrape_asx_tickers():
    url = "https://www.marketindex.com.au/asx-listed-companies"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tickers = []

    rows = soup.select("table tbody tr")
    if not rows:
        print("[ERROR] No ticker rows found. Falling back to static list.")
        return [
            'CBA.AX', 'BHP.AX', 'CSL.AX', 'NAB.AX', 'WBC.AX',
            'ANZ.AX', 'WOW.AX', 'TLS.AX', 'WDS.AX', 'FMG.AX'
        ]

    for row in rows:
        cols = row.find_all("td")
        if cols:
            ticker = cols[0].text.strip() + ".AX"
            tickers.append(ticker)

    print(f"[INFO] Scraped {len(tickers)} ASX tickers.")
    return tickers