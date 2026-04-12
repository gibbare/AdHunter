"""
Kamerastore scraper – kamerastore.com (säljer uteslutande begagnat).
Använder Shopify Predictive Search API (/search/suggest.json) som ger
bättre relevans än söksidan.

Söktermen saneras innan API-anropet:
  - Fästebeteckningar (ef, rf, fe …) tas bort
  - Ensamma brännviddssiffror (500, 600) kompletteras med "mm"
  - Enkla tecken filtreras bort
Exempel: "Canon EF 500 f/4" → "canon 500mm"
"""
import re
import requests
from typing import Optional
from scrapers._match import matches as _matches, MOUNT_WORDS

BASE = "https://kamerastore.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept": "application/json",
}


def _sanitize(query: str) -> str:
    """Förenkla söktermen för Shopifys predictive-API."""
    norm = re.sub(r"[^a-z0-9]", " ", query.lower())
    words = norm.split()
    words = [w for w in words if w not in MOUNT_WORDS]              # ta bort fästen
    words = [w + "mm" if re.fullmatch(r"\d{2,4}", w) else w for w in words]  # 500 → 500mm
    words = [w for w in words if len(w) > 1]                        # ta bort enkla tecken
    return " ".join(words)


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    sanitized = _sanitize(query)
    if not sanitized:
        return []

    try:
        resp = requests.get(
            f"{BASE}/en-se/search/suggest.json",
            params={"q": sanitized, "resources[type]": "product", "resources[limit]": 10},
            headers=HEADERS, timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"[Kamerastore] Fel vid hämtning: {e}")
        return []

    products = resp.json().get("resources", {}).get("results", {}).get("products", [])
    results = []

    for p in products:
        title = p.get("title", "").strip()
        if not title or not _matches(title, query):
            continue

        url = p.get("url", "")
        if not url.startswith("http"):
            url = BASE + url

        try:
            price_num = float(p.get("price", 0) or 0)
            if max_price and price_num > max_price:
                continue
            if min_price and price_num < min_price:
                continue
            price_str = f"{price_num:,.0f} SEK".replace(",", " ")
        except (ValueError, TypeError):
            price_str = ""

        pid = p.get("id") or re.sub(r"[^a-z0-9]", "_", url.lower())[-40:]

        results.append({
            "id":    f"ks_{pid}",
            "title": title,
            "price": price_str,
            "url":   url,
            "site":  "Kamerastore",
            "date":  "",
        })

    return results
