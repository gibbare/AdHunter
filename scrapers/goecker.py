"""
Goecker scraper – goecker.se/begagnat
DynamicWeb CMS (Swift-tema). Hämtar alla begagnade produkter (PageSize=100)
och filtrerar lokalt med _matches() eftersom det saknas sökning i begagnat-
sektionen.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

BASE = "https://goecker.se"
SEARCH_URL = f"{BASE}/begagnat"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "sv-SE,sv;q=0.9",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    try:
        resp = requests.get(SEARCH_URL, params={"PageSize": 100},
                            headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Goecker] Fel vid hämtning: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for art in soup.select("article.product-list-item"):
        title_el = art.select_one("[itemprop='name']")
        link_el  = art.select_one("a[href]")
        price_el = art.select_one(".text-price, [itemprop='price']")

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        href  = link_el["href"]
        url   = href if href.startswith("http") else BASE + href

        # Hämta pris: föredra content-attributet (rent tal) annars text
        if price_el and price_el.name == "span" and price_el.get("content"):
            price_num_str = price_el["content"]
            price = f"{float(price_num_str):,.0f} SEK".replace(",", " ")
        else:
            price = price_el.get_text(strip=True).replace("\xa0", " ") if price_el else ""

        if not _matches(title, query):
            continue

        # Prisfilter
        try:
            raw_num = float(re.sub(r"[^\d.]", "",
                                   price.replace(" ", "").replace(",", ".")))
            if max_price and raw_num > max_price:
                continue
            if min_price and raw_num < min_price:
                continue
        except (ValueError, TypeError):
            pass

        pid = art.get("data-product-id") or href.rstrip("/").split("/")[-1]

        results.append({
            "id":    f"goecker_{re.sub(r'[^a-z0-9]', '_', pid.lower())}",
            "title": title,
            "price": price,
            "url":   url,
            "site":  "Goecker",
            "date":  "",
        })

    return results


def _matches(title: str, query: str) -> bool:
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", " ", s.lower())
    title_norm  = normalize(title)
    query_words = [w for w in normalize(query).split() if len(w) > 1]
    return all(w in title_norm for w in query_words)
