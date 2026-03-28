"""
MPB scraper – mpb.com/en-gb
MPB exponerar ett JSON-API för sökresultat.
"""
import requests
from typing import Optional

BASE_URL = "https://www.mpb.com/api/products/search"
SITE_URL = "https://www.mpb.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.mpb.com/en-gb/",
}


def search(query: str, max_price: Optional[int] = None, min_price: Optional[int] = None) -> list[dict]:
    params = {
        "q": query,
        "locale": "en-gb",
        "page": 1,
        "perPage": 30,
        "sort": "newest",
    }
    if max_price:
        params["maxPrice"] = max_price
    if min_price:
        params["minPrice"] = min_price

    try:
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[MPB] Fel vid hämtning: {e}")
        return []

    results = []
    products = data.get("products") or data.get("items") or data.get("results") or []
    for p in products:
        slug  = p.get("slug") or p.get("sku") or ""
        title = p.get("title") or p.get("name") or p.get("displayName") or ""
        price = str(p.get("price") or p.get("sellingPrice") or "")
        url   = f"{SITE_URL}/en-gb/product/{slug}" if slug else SITE_URL
        pid   = str(p.get("id") or p.get("sku") or slug)

        if title and pid:
            results.append({
                "id":    f"mpb_{pid}",
                "title": title,
                "price": f"£{price}" if price else "",
                "url":   url,
                "site":  "MPB",
                "date":  "",
            })

    return results
