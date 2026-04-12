"""
Gemensam relevansfiltrering för alla scrapers.

Regler:
- Alla ord i söktermen (längd > 1) måste finnas i titeln …
- … UTOM kända objektivfästebeteckningar (ef, rf, fe, …) som är
  valfria OM titeln innehåller en brännviddsbeteckning (t.ex. "500mm").
  Butiker utelämnar ofta fästebeteckningen i linstitlar men inte i
  kamerakroppar, så regeln diskriminerar korrekt:
    "Canon 500mm f/4 L IS" matchar "Canon EF 500 f/4"  ✓
    "Canon EOS 500"        matchar INTE "Canon EF 500 f/4"  ✓
- Siffror matchas som delsträng ("500" hittas i "500mm").
"""

import re

# Objektivfästebeteckningar som butiker ofta utelämnar i produktnamn
MOUNT_WORDS: frozenset[str] = frozenset({
    "ef", "efs", "rf", "rfs",   # Canon
    "fe", "sel",                 # Sony
    "af", "ais", "afd",          # Nikon
    "m42", "m43", "mft",         # Universella
})

# Mönster: brännvidd angiven i mm (t.ex. "500mm", "85 mm")
_FOCAL_RE = re.compile(r"\d+\s*mm")


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", " ", s.lower())


def matches(title: str, query: str) -> bool:
    """
    Returnerar True om titeln är relevant för söktermen.
    Fästebeteckningar (ef, rf, fe …) behandlas som valfria när
    titeln innehåller en brännviddsbeteckning (nnmm).
    """
    title_norm    = _normalize(title)
    has_focal_len = bool(_FOCAL_RE.search(title_norm))

    all_words = [w for w in _normalize(query).split() if len(w) > 1]

    for w in all_words:
        if w in title_norm:
            continue                          # ordet finns → OK
        if w in MOUNT_WORDS and has_focal_len:
            continue                          # fästebeteckning i linstittel → OK
        return False                          # obligatoriskt ord saknas

    # Inga ord alls → ingen match
    return bool(all_words)

