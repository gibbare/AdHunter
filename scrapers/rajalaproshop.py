"""
Rajala Pro Shop scraper – rajalaproshop.se/swap-it
Använder Klevu-sök-API:t direkt (API-nyckel är publik i sidans HTML).
Söker enbart i SWAP IT!-sektionen (begagnat).

OBS: API:et returnerar XML, inte JSON.
"""
import requests
import xml.etree.ElementTree as ET
from typing import Optional
from scrapers._match import matches as _matches

KLEVU_API    = "https://eucs31.ksearchnet.com/cloud-search/n-search/search"
KLEVU_TICKET = "klevu-166912949174715814"
BASE_URL     = "https://www.rajalaproshop.se"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:

    params = {
        "ticket":       KLEVU_TICKET,
        "term":         query,
        "noOfResults":  50,
        "sv":           "20160801",
        "typeOfSearch": "DEFAULT",
        "sort":         "NEW_ARRIVALS",
    }

    try:
        resp = requests.get(KLEVU_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception as e:
        print(f"[Rajala] API-fel: {e}")
        return []

    results = []

    for r in root.findall("result"):
        name     = (r.findtext("name") or "").strip()
        url      = (r.findtext("url") or "").strip()
        price    = (r.findtext("salePrice") or r.findtext("price") or "").strip()
        pid      = (r.findtext("id") or url).strip()
        category = (r.findtext("category") or "").lower()
        usedgear = (r.findtext("usedgear") or "").strip().lower()

        if not name or not url:
            continue

        # Filtrera bort nya produkter – vi vill bara ha begagnade
        url_low = url.lower()
        is_used = (
            usedgear == "yes"
            or "swap it" in category
            or "begagna" in category
            or "begagna" in url_low
            or "swap" in url_low
        )
        if not is_used:
            continue

        # Filtrera bort produkter som inte matchar söktermen
        if not _matches(name, query):
            continue

        # Prisfilter (SEK)
        try:
            price_val = float(price.replace(" ", "").replace(",", "."))
            if max_price and price_val > max_price:
                continue
            if min_price and price_val < min_price:
                continue
        except (ValueError, TypeError):
            pass

        full_url  = url if url.startswith("http") else BASE_URL + url
        try:
            price_str = f"{int(float(price.replace(',', '.'))):,} kr".replace(",", " ") if price else ""
        except (ValueError, TypeError):
            price_str = ""

        results.append({
            "id":    f"rajala_{pid}",
            "title": name,
            "price": price_str,
            "url":   full_url,
            "site":  "Rajala Pro Shop",
            "date":  "",
        })

    return results


