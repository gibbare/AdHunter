"""
Cyberphoto scraper – använder Klevu sökning (deras inbyggda sök-API).
Produktresultat filtreras på is_used=True för att bara visa begagnat.
"""
import re
import requests
from typing import Optional
from scrapers._match import MOUNT_WORDS

KLEVU_ENDPOINT = "https://uscs32v2.ksearchnet.com/cs/v2/search"
KLEVU_API_KEY  = "klevu-169761350968416815"
BASE           = "https://www.cyberphoto.se"

# Märken som Cyberphoto utelämnar ur produkttitlar
_BRANDS = frozenset({
    "canon", "nikon", "sony", "fujifilm", "fuji", "olympus", "panasonic",
    "leica", "sigma", "tamron", "tokina", "samyang", "zeiss", "pentax",
    "minolta", "ricoh", "hasselblad",
})
# Ord som aldrig krävs i Cyberphotos titlar
_SKIP = MOUNT_WORDS | _BRANDS

HEADERS = {
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Content-Type":  "application/json",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    payload = {
        "context": {"apiKeys": [KLEVU_API_KEY]},
        "recordQueries": [{
            "id": "q",
            "typeOfRequest": "SEARCH",
            "settings": {
                "query": {"term": query},
                "typeOfRecords": ["KLEVU_PRODUCT"],
                "limit": 100,
                "offset": 0,
            }
        }]
    }
    try:
        resp = requests.post(KLEVU_ENDPOINT, json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Cyberphoto] Fel vid hämtning: {e}")
        return []

    data = resp.json()
    records = data.get("queryResults", [{}])[0].get("records", [])

    results = []
    for rec in records:
        # Filtrera: bara begagnade produkter
        if rec.get("is_used") != "True" and rec.get("condition", "").lower() != "used":
            continue

        title = rec.get("name", "").strip()
        if not title or not _cp_matches(title, query):
            continue

        url = rec.get("url", "")
        if not url.startswith("http"):
            url = BASE + url

        try:
            price_num = float(rec.get("salePrice") or rec.get("price") or 0)
            if max_price and price_num > max_price:
                continue
            if min_price and price_num < min_price:
                continue
            price_str = f"{price_num:,.0f} SEK".replace(",", " ")
        except (ValueError, TypeError):
            price_str = ""

        pid = rec.get("id") or re.sub(r"[^a-z0-9]", "_", url.lower())[-40:]

        results.append({
            "id":    f"cp_{pid}",
            "title": title,
            "price": price_str,
            "url":   url,
            "site":  "Cyberphoto",
            "date":  "",
        })

    return results


def _cp_matches(title: str, query: str) -> bool:
    """Cyberphoto-specifik: kräver modellsiffror/-namn men ignorerar
    märkesnamn (canon, sony …) och fästebeteckningar (ef, rf, fe …)
    eftersom Cyberphoto utelämnar dessa i produkttitlar."""
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]", " ", s.lower())
    title_n  = norm(title)
    required = [w for w in norm(query).split() if len(w) > 1 and w not in _SKIP]
    if not required:
        return True
    return all(w in title_n for w in required)
