"""
Kamerastore scraper – kamerastore.com/en-se/shop?condition=used
Använder Shopify Dawn-tema; produktkort har klassen .card-wrapper.
Söktermen filtrerar inte på serversidan → relevansfiltret _matches()
tar hand om det.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

BASE = "https://www.kamerastore.com"
SEARCH_URL = f"{BASE}/en-se/shop"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    params = {"condition": "used", "search": query}
    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Kamerastore] Fel vid hämtning: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for card in soup.select(".card-wrapper"):
        title_el = card.select_one(".card__heading a, h3 a, h2 a")
        price_el = card.select_one(".price-item--regular, .price__regular .price-item")
        link_el  = card.select_one("a.full-unstyled-link, a[href*='/products/']")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        href  = (link_el or title_el)["href"]
        url   = href if href.startswith("http") else BASE + href
        price = price_el.get_text(strip=True).replace("\xa0", " ") if price_el else ""
        # Rensa dubbel-text som "Regular price1 854.00 SEK"
        price = re.sub(r"^[^0-9]*", "", price).strip()

        if not _matches(title, query):
            continue

        # Prisfilter
        try:
            price_num = float(re.sub(r"[^\d.]", "", price.replace(",", ".")))
            if max_price and price_num > max_price:
                continue
            if min_price and price_num < min_price:
                continue
        except (ValueError, TypeError):
            pass

        pid = url.rstrip("/").split("/")[-1]

        results.append({
            "id":    f"ks_{pid}",
            "title": title,
            "price": price,
            "url":   url,
            "site":  "Kamerastore",
            "date":  "",
        })

    return results


def _matches(title: str, query: str) -> bool:
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", " ", s.lower())
    title_norm  = normalize(title)
    query_words = [w for w in normalize(query).split() if len(w) > 1]
    return all(w in title_norm for w in query_words)
