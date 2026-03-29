"""
MPB scraper – mpb.com
MPB blockerar API-anrop med 403. Försöker HTML-scraping av söksidan
som fallback. Misslyckas tyst om sidan är skyddad.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

BASE_URL  = "https://www.mpb.com"
SEARCH_URL = f"{BASE_URL}/en-eu/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.mpb.com/",
}


def search(query: str, max_price: Optional[int] = None,
           min_price: Optional[int] = None) -> list[dict]:
    params = {"search": query}
    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS,
                            timeout=15, allow_redirects=True)
        if resp.status_code == 403:
            print(f"[MPB] Åtkomst nekad (403) – sidan blockerar automatiska förfrågningar.")
            return []
        resp.raise_for_status()
    except Exception as e:
        print(f"[MPB] Fel vid hämtning: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # MPB använder Next.js – produktdata kan ligga i __NEXT_DATA__ JSON
    import json
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        try:
            data = json.loads(next_data.string)
            products = (data.get("props", {})
                            .get("pageProps", {})
                            .get("searchResults", {})
                            .get("products") or [])
            for p in products:
                title = p.get("title") or p.get("name") or ""
                slug  = p.get("slug") or p.get("sku") or ""
                price = str(p.get("price") or p.get("sellingPrice") or "")
                url   = f"{BASE_URL}/en-eu/product/{slug}" if slug else BASE_URL
                pid   = str(p.get("id") or slug)

                if not title or not pid:
                    continue
                if not _matches(title, query):
                    continue

                try:
                    price_num = float(price)
                    if max_price:
                        # MPB priser är i GBP, konvertera grovt (~13 SEK/GBP)
                        if price_num * 13 > max_price:
                            continue
                    if min_price:
                        if price_num * 13 < min_price:
                            continue
                except (ValueError, TypeError):
                    pass

                results.append({
                    "id":    f"mpb_{pid}",
                    "title": title,
                    "price": f"£{price}" if price else "",
                    "url":   url,
                    "site":  "MPB",
                    "date":  "",
                })
            return results
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback: HTML-scraping
    for card in soup.select("[class*='ProductCard'], [class*='product-card'], article"):
        title_el = card.select_one("h2, h3, [class*='title'], [class*='name']")
        price_el = card.select_one("[class*='price']")
        link_el  = card.select_one("a[href]")

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        href  = link_el["href"]
        url   = href if href.startswith("http") else BASE_URL + href
        price = price_el.get_text(strip=True) if price_el else ""
        pid   = url.rstrip("/").split("/")[-1]

        if not _matches(title, query):
            continue

        results.append({
            "id":    f"mpb_{pid}",
            "title": title,
            "price": price,
            "url":   url,
            "site":  "MPB",
            "date":  "",
        })

    return results


def _matches(title: str, query: str) -> bool:
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", " ", s.lower())
    title_norm  = normalize(title)
    query_words = [w for w in normalize(query).split() if len(w) > 1]
    return all(w in title_norm for w in query_words)
