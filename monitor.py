#!/usr/bin/env python3
"""
Ad Monitor – bevaka annonser på Blocket, MPB, Kamerastore,
Scandinavian Photo, Cyberphoto och Goecker.

Kör: python monitor.py
Redigera söktermer i config.json
"""
import json
import os
import time
import sys
from datetime import datetime
from pathlib import Path

from notifier import send_telegram, format_ad
from scrapers import blocket, mpb, kamerastore, scandinavianphoto, cyberphoto, goecker

CONFIG_FILE  = Path(__file__).parent / "config.json"
SEEN_FILE    = Path(__file__).parent / "seen_ads.json"

SCRAPERS = {
    "blocket":          blocket.search,
    "mpb":              mpb.search,
    "kamerastore":      kamerastore.search,
    "scandinavianphoto": scandinavianphoto.search,
    "cyberphoto":       cyberphoto.search,
    "goecker":          goecker.search,
}


# ──────────────────────────────────────────────
# Hjälpfunktioner
# ──────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_seen() -> set:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, indent=2)


def check_config(cfg: dict) -> bool:
    """Kontrollerar att konfigurationen är ifylld."""
    tg = cfg.get("telegram", {})
    if not tg.get("token") or tg["token"] == "DIN_BOT_TOKEN_HÄR":
        print("❌  Fyll i din Telegram-token i config.json (se README.txt)")
        return False
    if not tg.get("chat_id") or tg["chat_id"] == "DITT_CHAT_ID_HÄR":
        print("❌  Fyll i ditt Telegram chat_id i config.json (se README.txt)")
        return False
    if not cfg.get("search_terms"):
        print("❌  Inga söktermer i config.json")
        return False
    return True


# ──────────────────────────────────────────────
# Huvud-loop
# ──────────────────────────────────────────────

def run_check(cfg: dict, seen: set) -> int:
    """
    Kör en omgång sökningar mot alla aktiverade sajter.
    Returnerar antalet nya annonser som hittades.
    """
    token      = cfg["telegram"]["token"]
    chat_id    = cfg["telegram"]["chat_id"]
    sites      = cfg.get("sites", {})
    max_price  = cfg.get("max_price_sek")
    min_price  = cfg.get("min_price_sek")
    new_count  = 0

    for term in cfg["search_terms"]:
        print(f"  🔍 Söker efter: {term}")
        for site_name, scraper_fn in SCRAPERS.items():
            if not sites.get(site_name, True):
                continue
            try:
                ads = scraper_fn(term, max_price, min_price)
            except Exception as e:
                print(f"    [{site_name}] Oväntat fel: {e}")
                ads = []

            for ad in ads:
                uid = f"{site_name}::{ad['id']}"
                if uid in seen:
                    continue

                # Ny annons!
                seen.add(uid)
                new_count += 1
                msg = format_ad(ad, term)
                print(f"    ✅ Ny: [{ad['site']}] {ad['title']} – {ad.get('price','')}")
                send_telegram(token, chat_id, msg)
                time.sleep(0.5)  # Undvik att spamma Telegram-API:et

    return new_count


def main() -> None:
    print("=" * 55)
    print("  Ad Monitor – Annonsbevakning")
    print("=" * 55)

    cfg = load_config()
    if not check_config(cfg):
        sys.exit(1)

    interval_sec = int(cfg.get("check_interval_minutes", 20)) * 60
    seen = load_seen()

    print(f"✅  Kör med {len(cfg['search_terms'])} sökterm(er)")
    print(f"⏱️   Kontrollintervall: {cfg.get('check_interval_minutes', 20)} minuter")
    print(f"📡  Aktiva sajter: {', '.join(s for s, v in cfg.get('sites', {}).items() if v)}")
    print(f"📋  Sedan tidigare kända annonser: {len(seen)}")
    print("-" * 55)

    # Skicka ett testmeddelande vid start
    send_telegram(cfg["telegram"]["token"], cfg["telegram"]["chat_id"],
                  "🚀 <b>Ad Monitor startad!</b>\n"
                  f"Söker efter: {', '.join(cfg['search_terms'])}\n"
                  f"Intervall: {cfg.get('check_interval_minutes', 20)} min")

    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] Söker...")
        new = run_check(cfg, seen)
        save_seen(seen)
        print(f"[{now}] Klart – {new} nya annonser. Väntar {cfg.get('check_interval_minutes', 20)} min...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStoppad av användaren. Hejdå!")
