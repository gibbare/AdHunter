"""
Rajala Pro Shop scraper – rajalaproshop.se/swap-it
Använder Klevu-sök-API:t direkt (API-nyckel är publik i sidans HTML).
Söker enbart i SWAP IT!-sektionen (begagnat).
"""
import requests
from typing import Optional

KLEVU_API    = "https://eucs31.ksearchnet.com/cloud-search/n-search/search"
KLEVU_TICKET = "klevu-166912949174715814"
BASE_URL     = "https://www.rajalaproshop.se"

# Kategori-ID:n för begagnat-sektionen
SWAP_IT_CATEGORIES = ["SWAP IT!", "Begagnade kameror", "Begagnade objektiv",
                      "Begagnat tillbehör", "Begagnade objektiv"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept": "application/json",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:

    params = {
        "ticket":        KLEVU_TICKET,
        "term":          query,
        "noOfResults":   50,
        "sv":            "20160801",
        "typeOfSearch":  "DEFAULT",
        "sort":          "NEW_ARRIVALS",
        # Begränsa till SWAP IT!-kategorin (id 209)
        "category":      "SWAP IT!",
        "enableFilters": "true",
    }

    try:
        resp = requests.get(KLEVU_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Rajala] API-fel: {e}")
        return []

    results = []

    # Klevu returnerar resultaten under queryResults[0].records
    query_results = data.get("queryResults") or []
    records = []
    for qr in query_results:
        records.extend(qr.get("records") or [])

    for r in records:
        name  = r.get("name") or r.get("klevu_product_variant") or ""
        url   = r.get("url") or ""
        price = r.get("salePrice") or r.get("price") or ""
        pid   = r.get("id") or r.get("itemGroupId") or url

        if not name or not url:
            continue

        # Filtrera bort nya produkter – vi vill bara ha begagnade
        # Begagnade produkter brukar ha "swap" eller "begagna" i URL eller kategori
        cats  = str(r.get("category") or "").lower()
        u_low = url.lower()
        if "swap" not in cats and "swap" not in u_low and "begagna" not in u_low:
            continue

        # Prisfilter (SEK)
        try:
            price_val = float(str(price).replace(" ", "").replace(",", "."))
            if max_price and price_val > max_price:
                continue
            if min_price and price_val < min_price:
                continue
        except (ValueError, TypeError):
            pass

        full_url = url if url.startswith("http") else BASE_URL + url
        price_str = f"{int(float(str(price).replace(',','.')):,.0f} kr" if price else ""

        results.append({
            "id":    f"rajala_{pid}",
            "title": name,
            "price": price_str,
            "url":   full_url,
            "site":  "Rajala Pro Shop",
            "date":  "",
        })

    return results
