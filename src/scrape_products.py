from pathlib import Path
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://books.toscrape.com/"
MAX_PAGES = 3
OUT = Path("data/scraped_products.csv")
HEADERS = {"User-Agent": "StudentDataAnalyticsProject/1.0 (educational use)"}

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    url = BASE
    rows = []
    for _ in range(MAX_PAGES):
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select("article.product_pod"):
            title_tag = item.select_one("h3 a")
            price_tag = item.select_one(".price_color")
            if not title_tag or not price_tag:
                continue
            title = title_tag.get("title") or title_tag.get_text(strip=True)
            product_url = urljoin(url, title_tag.get("href", ""))
            price_text = price_tag.get_text(strip=True).replace("£", "").replace("Â", "")
            try:
                price = float(price_text)
            except ValueError:
                continue
            rows.append({"product_name": title, "price_gbp": price, "product_url": product_url})
        next_link = soup.select_one("li.next a")
        if not next_link:
            break
        url = urljoin(url, next_link.get("href"))
        time.sleep(1)
    df = pd.DataFrame(rows).drop_duplicates(subset=["product_url"])
    if df.empty:
        raise RuntimeError("No products scraped. Check internet access or the demo site's HTML.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} products to {OUT}")

if __name__ == "__main__":
    main()
