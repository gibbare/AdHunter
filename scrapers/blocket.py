"""
Blocket scraper – använder den officiella RSS-feeden.
URL-format: https://www.blocket.se/annonser/hela_sverige?rss=1&q=QUERY
"""
import xml.etree.ElementTree as ET
import requests
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
}


def search(query: str, max_price: Optional[int] = None, min_price: Optional[int] = None) -> list[dict]:
    url = f"https://www.blocket.se/annonser/hela_sverige?rss=1&q={requests.utils.quote(query)}"
    if max_price:
        url += f"&price_to={max_price}"
    if min_price:
        url += f"&price_from={min_price}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Blocket] Fel vid hämtning: {e}")
        return []

    results = []
    try:
        root = ET.fromstring(resp.content)
        ns = {"media": "http://search.yahoo.com/mrss/"}
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            price_tag = item.find("media:price", ns)
            price = price_tag.text.strip() if price_tag is not None else ""
            pub_date = item.findtext("pubDate", "").strip()

            if title and link:
                results.append({
                    "id":     link.split("/")[-1].split("?")[0],
                    "title":  title,
                    "price":  price,
                    "url":    link,
                    "site":   "Blocket",
                    "date":   pub_date,
                })
    except ET.ParseError as e:
        print(f"[Blocket] XML-parse-fel: {e}")

    return results
