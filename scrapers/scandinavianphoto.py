"""
Scandinavian Photo scraper – scandinavianphoto.se/second-hand / begagnat
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional
import re

BASE = "https://www.scandinavianphoto.se"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "sv-SE,sv;q=0.9",
}


def search(query: str, max_price: Optional[int] = None, min_price: Optional[int] = None) -> list[dict]:
    # Prova söksidan först
    url = f"{BASE}/search?query={requests.utils.quote(query)}&second_hand=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ScandinavianPhoto] Fel vid hämtning: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for card in soup.select(".product-card, .product-item, article.product, li.item"):
        title_el = card.select_one("h2, h3, .product-name, .product-title, a[title]")
        link_el  = card.select_one("a[href]")
        price_el = card.select_one(".price, .product-price, [class*='price']")

        if not (title_el and link_el):
            continue

        title = title_el.get_text(strip=True)
        href  = link_el["href"]
        url_  = href if href.startswith("http") else BASE + href
        price = price_el.get_text(strip=True) if price_el else ""
        pid   = re.sub(r"[^a-z0-9]", "_", url_.lower())[-60:]

        if not _matches(title, query):
            continue

        results.append({
            "id":    f"sp_{pid}",
            "title": title,
            "price": price,
            "url":   url_,
            "site":  "Scandinavian Photo",
            "date":  "",
        })

    return results


def _matches(title: str, query: str) -> bool:
    words = query.lower().split()
    t = title.lower()
    return all(w in t for w in words)
