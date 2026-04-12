"""
Scandinavian Photo scraper – /begagnat?pageSize=200
Produktkort: .sp-product-card, titel från img[alt], pris från [class*='price'].
Söktermen filtrerar inte på serversidan → _matches() filtrerar lokalt.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

BASE = "https://www.scandinavianphoto.se"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "sv-SE,sv;q=0.9",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    url = f"{BASE}/begagnat"
    try:
        resp = requests.get(url, params={"pageSize": 200}, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ScandinavianPhoto] Fel vid hämtning: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for card in soup.select(".sp-product-card"):
        img      = card.select_one("img[alt]")
        link_el  = card.select_one("a[href]")
        price_el = card.select_one("[class*='price']")

        if not img or not link_el:
            continue

        title = img.get("alt", "").strip()
        if not title or not _matches(title, query):
            continue

        href  = link_el["href"]
        url_  = href if href.startswith("http") else BASE + href
        price = price_el.get_text(strip=True).replace("\xa0", " ") if price_el else ""
        pid   = re.sub(r"[^a-z0-9]", "_", url_.lower())[-60:]

        # Prisfilter
        try:
            price_num = float(re.sub(r"[^\d]", "", price.split("SEK")[0].replace(" ", "")))
            if max_price and price_num > max_price:
                continue
            if min_price and price_num < min_price:
                continue
        except (ValueError, TypeError):
            pass

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
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", " ", s.lower())
    title_norm  = normalize(title)
    query_words = [w for w in normalize(query).split() if len(w) > 1]
    return all(w in title_norm for w in query_words)
