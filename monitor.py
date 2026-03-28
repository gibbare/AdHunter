#!/usr/bin/env python3
"""
Ad Monitor – bevaka annonser på Blocket, MPB, Kamerastore,
Scandinavian Photo, Cyberphoto och Goecker.

Lokalt:        python monitor.py
GitHub Actions: körs automatiskt via workflow – kör en gång och avslutar.

Telegram-hemligheter läses från miljövariabler (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
i första hand, och faller tillbaka på config.json om de saknas.
"""
import json
import os
import time
import sys
from datetime import datetime
from pathlib import Path

from notifier import send_telegram, format_ad
from scrapers import blocket, mpb, kamerastore, scandinavianphoto, cyberphoto, goecker

CONFIG_FILE = Path(__file__).parent / "config.json"
SEEN_FILE   = Path(__file__).parent / "seen_ads.json"

SCRAPERS = {
    "blocket":           blocket.search,
    "mpb":               mpb.search,
    "kamerastore":       kamerastore.search,
    "scandinavianphoto": scandinavianphoto.search,
    "cyberphoto":        cyberphoto.search,
    "goecker":           goecker.search,
}


# ──────────────────────────────────────────────
# Hjälpfunktioner
# ──────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)

    # Miljövariabler (GitHub Secrets) åsidosätter config.json
    token   = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token:
        cfg.setdefault("telegram", {})["token"]   = token
    if chat_id:
        cfg.setdefault("telegram", {})["chat_id"] = chat_id

    return cfg


def load_seen() -> set:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, indent=2)


def check_config(cfg: dict) -> bool:
    tg = cfg.get("telegram", {})
    if not tg.get("token"):
        print("❌  TELEGRAM_TOKEN saknas. Sätt den som GitHub Secret eller i config.json.")
        return False
    if not tg.get("chat_id"):
        print("❌  TELEGRAM_CHAT_ID saknas. Sätt den som GitHub Secret eller i config.json.")
        return False
    if not cfg.get("search_terms"):
        print("❌  Inga söktermer i config.json")
        return False
    return True


# ──────────────────────────────────────────────
# Sökrunda
# ──────────────────────────────────────────────

def run_check(cfg: dict, seen: set) -> int:
    token     = cfg["telegram"]["token"]
    chat_id   = cfg["telegram"]["chat_id"]
    sites     = cfg.get("sites", {})
    max_price = cfg.get("max_price_sek")
    min_price = cfg.get("min_price_sek")
    new_count = 0

    for term in cfg["search_terms"]:
        print(f"  🔍 Söker: {term}")
        for site_name, scraper_fn in SCRAPERS.items():
            if not sites.get(site_name, True):
                continue
            try:
                ads = scraper_fn(term, max_price, min_price)
            except Exception as e:
                print(f"    [{site_name}] Fel: {e}")
                ads = []

            for ad in ads:
                uid = f"{site_name}::{ad['id']}"
                if uid in seen:
                    continue
                seen.add(uid)
                new_count += 1
                print(f"    ✅ Ny: [{ad['site']}] {ad['title']} – {ad.get('price', '')}")
                send_telegram(token, chat_id, format_ad(ad, term))
                time.sleep(0.5)

    return new_count


# ──────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────

def main() -> None:
    # Kör-läge: "once" i CI/GitHub Actions, annars kontinuerlig loop lokalt
    once = os.environ.get("RUN_ONCE", "").lower() in ("1", "true", "yes")

    print("=" * 55)
    print("  Ad Monitor – Annonsbevakning")
    print("=" * 55)

    cfg = load_config()
    if not check_config(cfg):
        sys.exit(1)

    seen = load_seen()
    print(f"📋  Kända annonser sedan tidigare: {len(seen)}")
    print(f"🔎  Söktermer: {', '.join(cfg['search_terms'])}")
    print(f"📡  Sajter: {', '.join(s for s, v in cfg.get('sites', {}).items() if v)}")
    print("-" * 55)

    if once:
        # GitHub Actions-läge – kör en gång och avsluta
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        print(f"[{now}] Kör en gång (CI-läge)...")
        new = run_check(cfg, seen)
        save_seen(seen)
        print(f"Klart – {new} nya annonser hittades.")
    else:
        # Lokalt läge – loop med intervall
        interval_sec = int(cfg.get("check_interval_minutes", 20)) * 60
        print(f"⏱️  Intervall: {cfg.get('check_interval_minutes', 20)} min  (Ctrl+C för att stoppa)\n")
        while True:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] Söker...")
            new = run_check(cfg, seen)
            save_seen(seen)
            print(f"[{now}] Klart – {new} nya. Väntar {cfg.get('check_interval_minutes', 20)} min...")
            time.sleep(interval_sec)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStoppad. Hejdå!")
