"""
Notifier – skickar meddelanden via Telegram.

Instruktioner för att sätta upp:
1. Öppna Telegram och sök efter "@BotFather"
2. Skicka /newbot och följ instruktionerna → du får ett TOKEN
3. Starta en chatt med din bot (sök på botnamnet och klicka Start)
4. Hämta ditt chat_id:
   Öppna https://api.telegram.org/bot<DIN_TOKEN>/getUpdates i webbläsaren
   Skicka ett meddelande till boten och ladda om sidan.
   Leta efter "id" under "chat" – det är ditt chat_id.
5. Fyll i token och chat_id i config.json
"""
import requests


def send_telegram(token: str, chat_id: str, message: str) -> bool:
    """Skickar ett meddelande via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Notifier] Telegram-fel: {e}")
        return False


def format_ad(ad: dict, search_term: str) -> str:
    """Formaterar en annons till ett Telegram-meddelande."""
    lines = [
        f"🔔 <b>Ny annons – {ad['site']}</b>",
        f"🔍 Sökning: <i>{search_term}</i>",
        f"📦 {ad['title']}",
    ]
    if ad.get("price"):
        lines.append(f"💰 {ad['price']}")
    if ad.get("date"):
        lines.append(f"📅 {ad['date']}")
    lines.append(f"🔗 <a href=\"{ad['url']}\">Öppna annons</a>")
    return "\n".join(lines)
