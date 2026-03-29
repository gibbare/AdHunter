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

import requests

from notifier import format_and_send
from scrapers import blocket, mpb, kamerastore, scandinavianphoto, cyberphoto, goecker, rajalaproshop

CONFIG_FILE = Path(__file__).parent / "config.json"
SEEN_FILE   = Path(__file__).parent / "seen_ads.json"

SCRAPERS = {
    "blocket":           blocket.search,
    "mpb":               mpb.search,
    "kamerastore":       kamerastore.search,
    "scandinavianphoto": scandinavianphoto.search,
    "cyberphoto":        cyberphoto.search,
    "goecker":           goecker.search,
    "rajalaproshop":     rajalaproshop.search,
}


# ──────────────────────────────────────────────
# Hjälpfunktioner
# ──────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)

    # Try fetching live config from Worker (overrides config.json terms/sites/interval)
    worker_url = os.environ.get("WORKER_URL", "").rstrip("/")
    notify_secret = os.environ.get("NOTIFY_SECRET", "")
    if worker_url and notify_secret:
        try:
            resp = requests.get(
                f"{worker_url}/config",
                params={"secret": notify_secret},
                timeout=10
            )
            if resp.status_code == 200:
                remote = resp.json()
                # Only override if there are terms defined remotely
                if remote.get("terms"):
                    cfg["search_terms"] = [
                        t["query"] for t in remote["terms"] if t.get("active", True)
                    ]
                if remote.get("sites"):
                    cfg["sites"] = remote["sites"]
                if remote.get("interval"):
                    cfg["check_interval_minutes"] = remote["interval"]
                print(f"  ✅ Config hämtad från Worker ({len(cfg['search_terms'])} aktiva termer)")
        except Exception as e:
            print(f"  ⚠️  Kunde inte hämta config från Worker: {e} – använder config.json")

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
    if not os.environ.get("WORKER_URL") and not cfg.get("worker_url"):
        print("❌  WORKER_URL saknas. Sätt den som miljövariabel i Railway.")
        return False
    if not os.environ.get("NOTIFY_SECRET") and not cfg.get("notify_secret"):
        print("❌  NOTIFY_SECRET saknas. Sätt den som miljövariabel i Railway.")
        return False
    if not cfg.get("search_terms"):
        print("❌  Inga söktermer i config.json")
        return False
    return True


# ──────────────────────────────────────────────
# Sökrunda
# ──────────────────────────────────────────────

def run_check(cfg: dict, seen: set) -> int:
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
                format_and_send(ad, term)
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
    worker = os.environ.get("WORKER_URL") or cfg.get("worker_url", "")
    print(f"📋  Kända annonser sedan tidigare: {len(seen)}")
    print(f"🔎  Söktermer: {', '.join(cfg['search_terms'])}")
    print(f"📡  Sajter: {', '.join(s for s, v in cfg.get('sites', {}).items() if v)}")
    print(f"🌐  Worker: {worker}")
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
