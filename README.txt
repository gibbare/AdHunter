============================================================
  Ad Monitor – Annonsbevakning för begagnad kamerautrustning
============================================================

Bevakar Blocket, MPB, Kamerastore, Scandinavian Photo,
Cyberphoto och Goecker. Skickar push-notiser via Telegram
när en ny annons dyker upp.

------------------------------------------------------------
STEG 1 – Installera Python-beroenden (kör EN gång)
------------------------------------------------------------

  pip install -r requirements.txt


------------------------------------------------------------
STEG 2 – Skapa en Telegram-bot (5 minuter, gratis)
------------------------------------------------------------

1. Öppna Telegram och sök efter @BotFather
2. Skicka:  /newbot
3. Välj ett namn och ett användarnamn (måste sluta på "bot")
4. Du får ett TOKEN, t.ex.:  1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   → Kopiera det

5. Sök upp DIN nya bot i Telegram och klicka "Start"
6. Öppna webbläsaren och klistra in:
     https://api.telegram.org/bot<DIN_TOKEN>/getUpdates
   Skicka ett meddelande till boten och ladda om sidan.
7. I JSON-svaret, leta upp "id" under "chat" – det är ditt CHAT_ID
   Exempel: "id": 98765432


------------------------------------------------------------
STEG 3 – Konfigurera config.json
------------------------------------------------------------

Öppna config.json i en texteditor och fyll i:

  "token":   "DIN_BOT_TOKEN_HÄR"    ← från steg 2
  "chat_id": "DITT_CHAT_ID_HÄR"     ← från steg 2

Lägg till dina söktermer:

  "search_terms": [
    "Sony A7 III",
    "Leica M6",
    "Canon EF 85mm"
  ]

Valfritt – filtrera på pris (i SEK, null = inget filter):

  "max_price_sek": 15000,
  "min_price_sek": 500

Stäng av sajter du inte vill bevaka:

  "sites": {
    "blocket":           true,
    "mpb":               true,
    "kamerastore":       true,
    "scandinavianphoto": true,
    "cyberphoto":        true,
    "goecker":           true
  }

Intervall (i minuter) hur ofta agenten söker:

  "check_interval_minutes": 20


------------------------------------------------------------
STEG 4 – Starta agenten
------------------------------------------------------------

  python monitor.py

Du bör se:
  ✅  Kör med X sökterm(er)
  ⏱️   Kontrollintervall: 20 minuter
  ...

Och ett Telegram-meddelande: "🚀 Ad Monitor startad!"


------------------------------------------------------------
KÖR I BAKGRUNDEN (Windows)
------------------------------------------------------------

Alternativ A – minimerat terminalfönster:
  Högerklicka på skrivbordet → Ny → Genväg
  Kommando: pythonw "C:\...\ad-monitor\monitor.py"

Alternativ B – Windows Task Scheduler:
  1. Öppna "Schemaläggaren" (Task Scheduler)
  2. Skapa grundläggande uppgift
  3. Program: python.exe
  4. Argument: "C:\sökväg\till\ad-monitor\monitor.py"
  5. Starta: Vid inloggning

Alternativ C – Kör som bakgrundsprocess i PowerShell:
  Start-Process pythonw -ArgumentList "monitor.py" -WorkingDirectory "C:\...\ad-monitor"


------------------------------------------------------------
FELSÖKNING
------------------------------------------------------------

"Ingen träff på [sajt]":
  → Sajten kan ha ändrat sin HTML-struktur.
     Öppna scrapers/<sajt>.py och justera CSS-selektorerna.

"Telegram-fel":
  → Kontrollera att token och chat_id är korrekta.
  → Testa länken: https://api.telegram.org/bot<TOKEN>/getMe

Blocket ger inga resultat:
  → RSS-feeden är beroende av att Blocket inte ändrat URL-format.
     Testa manuellt: https://www.blocket.se/annonser/hela_sverige?rss=1&q=sony


------------------------------------------------------------
FILER
------------------------------------------------------------

monitor.py          – Huvudskriptet, starta detta
config.json         – Din konfiguration (söktermer, API-nycklar)
seen_ads.json       – Automatiskt genererad, håller reda på seddda annonser
notifier.py         – Telegram-notifikationer
scrapers/           – En fil per sajt
requirements.txt    – Python-beroenden
README.txt          – Den här filen
============================================================
