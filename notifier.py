"""
Notifier – skickar web push via den befintliga Cloudflare Worker-endpointen /notify.

Miljövariabler (sätts i Railway):
  WORKER_URL     – t.ex. https://aurora-push.gibbare.workers.dev
  NOTIFY_SECRET  – samma hemliga nyckel som i Cloudflare Worker (NOTIFY_SECRET)
"""
import os
import requests

WORKER_URL    = os.environ.get("WORKER_URL", "").rstrip("/")
NOTIFY_SECRET = os.environ.get("NOTIFY_SECRET", "")


def send_push(title: str, body: str, tag: str, url: str) -> bool:
    """Skickar en push-notis via Cloudflare Worker /notify."""
    if not WORKER_URL or not NOTIFY_SECRET:
        print("[Notifier] WORKER_URL eller NOTIFY_SECRET saknas – ingen notis skickad.")
        return False
    try:
        resp = requests.post(
            f"{WORKER_URL}/notify",
            json={"secret": NOTIFY_SECRET, "title": title, "body": body, "tag": tag, "url": url},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"[Notifier] Push skickad till {data.get('sent', '?')} prenumerant(er).")
        return True
    except Exception as e:
        print(f"[Notifier] Fel: {e}")
        return False


def format_and_send(ad: dict, search_term: str) -> bool:
    title = f"📦 Ny annons – {ad['site']}"
    parts = [ad["title"]]
    if ad.get("price"):
        parts.append(ad["price"])
    parts.append(f"Sökning: {search_term}")
    body = " · ".join(parts)
    tag  = f"ad-{ad['id']}"[:32]
    return send_push(title, body, tag, ad["url"])
