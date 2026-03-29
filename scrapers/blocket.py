"""
Blocket scraper – använder den nya söksidan (RSS-feeden är borttagen).
URL-format: https://www.blocket.se/recommerce/forsale/search?q=QUERY
Produkterna finns inbäddade som JSON-LD i HTML-sidan.
"""
import json
import re
import requests
from typing import Optional

BASE = "https://www.blocket.se"
SEARCH_URL = f"{BASE}/recommerce/forsale/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "sv-SE,sv;q=0.9",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    params = {"q": query}
    if min_price:
        params["price_from"] = min_price
    if max_price:
        params["price_to"] = max_price

    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS,
                            timeout=15, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Blocket] Fel vid hämtning: {e}")
        return []

    # Extrahera JSON-LD med sökresultaten
    match = re.search(
        r'<script[^>]+id="seoStructuredData"[^>]*>(.*?)</script>',
        resp.text, re.DOTALL
    )
    if not match:
        print("[Blocket] Hittade inte seoStructuredData i sidan")
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"[Blocket] JSON-parse-fel: {e}")
        return []

    items = (data.get("mainEntity") or {}).get("itemListElement") or []
    results = []

    for entry in items:
        item = entry.get("item") or {}
        name  = (item.get("name") or item.get("description") or "").strip()
        url   = (item.get("url") or "").strip()
        price = str((item.get("offers") or {}).get("price") or "").strip()

        if not name or not url:
            continue

        # Annons-ID från URL
        pid = url.rstrip("/").split("/")[-1]

        # Klientside-prisfilter (fallback om URL-parametrar inte filtrerade)
        try:
            price_val = float(price.replace(" ", "").replace(",", "."))
            if max_price and price_val > max_price:
                continue
            if min_price and price_val < min_price:
                continue
        except (ValueError, TypeError):
            pass

        price_str = f"{int(float(price)):,} kr".replace(",", " ") if price else ""

        results.append({
            "id":    f"blocket_{pid}",
            "title": name,
            "price": price_str,
            "url":   url,
            "site":  "Blocket",
            "date":  "",
        })

    return results
