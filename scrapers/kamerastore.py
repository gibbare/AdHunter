"""
Kamerastore scraper – kamerastore.com (säljer uteslutande begagnat).
Använder söksidan /en-se/search?q=QUERY&type=product.
Produktkort: <product-card> custom element, titel + länk från a.product-card__link.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

BASE = "https://kamerastore.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    url = f"{BASE}/en-se/search"
    try:
        resp = requests.get(url, params={"q": query, "type": "product"},
                            headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Kamerastore] Fel vid hämtning: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for card in soup.select("product-card"):
        link_el  = card.select_one("a.product-card__link, a[href*='/products/']")
        price_el = card.select_one("[class*='price']")

        if not link_el:
            continue

        title = link_el.get_text(strip=True)
        if not title or not _matches(title, query):
            continue

        href  = link_el["href"]
        url_  = href if href.startswith("http") else BASE + href
        price = price_el.get_text(strip=True).replace("\xa0", " ") if price_el else ""

        # Prisfilter
        try:
            price_num = float(re.sub(r"[^\d.,]", "", price).replace(",", "."))
            if max_price and price_num > max_price:
                continue
            if min_price and price_num < min_price:
                continue
        except (ValueError, TypeError):
            pass

        pid = card.get("data-product-id") or re.sub(r"[^a-z0-9]", "_", url_.lower())[-40:]

        results.append({
            "id":    f"ks_{pid}",
            "title": title,
            "price": price,
            "url":   url_,
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
