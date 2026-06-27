#!/usr/bin/env python3
"""Convertitore Wikisource → Costituzione.md in formato italia-corpus.

Uso:
    python3 strumenti/converti-da-wikisource.py [--output OUTPUT]
    
Di default scrive Costituzione.md nella radice del repo.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger("converti-da-wikisource")

WIKISOURCE_URL = (
    "https://it.wikisource.org/w/index.php"
    "?title=Italia,_Repubblica_-_Costituzione&action=raw"
)

# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

FRONTMATTER = """\
---
tipo: COSTITUZIONE
numero: 1
data: 1947-12-27
titolo: "Costituzione della Repubblica Italiana"
urn: urn:nir:stato:costituzione:1947-12-27
codice_redazionale: 047U0001
vigente: true
fonte: https://it.wikisource.org/wiki/Italia,_Repubblica_-_Costituzione
licenza: CC BY-SA 3.0
---
"""

# ---------------------------------------------------------------------------
# Heading mapping: wikitext → Markdown
# ---------------------------------------------------------------------------

# Lista di (pattern_compilato, replacement) per conversione heading
HEADING_RULES: list[tuple[re.Pattern, str]] = [
    # ===== Art. N =====  →  ## Art. N (PRIMA: più specifico)
    (re.compile(r"^=====\s*(Art\.\s*\d+[^\s]*)\s*=====\s*$"), r"## \1"),
    # ==== Sezione ====  →  ### Sezione
    (re.compile(r"^====\s*(?!#)(.+?)\s*====\s*$"), r"### \1"),
    # === Titolo ===  →  ## Titolo
    (re.compile(r"^===\s*(?!#)(.+?)\s*===\s*$"), r"## \1"),
    # == '''Parte''' ==  →  # Parte
    (re.compile(r"^==\s*'''(?!#)(.+?)'''\s*==\s*$"), r"# \1"),
    # == Parte (non bold) == → # Parte  
    (re.compile(r"^==\s*(?!#)(.+?)\s*==\s*$"), r"# \1"),
]

# ---------------------------------------------------------------------------
# Pattern per riconoscere l'inizio del testo costituzionale
# ---------------------------------------------------------------------------

# Cerchiamo la formula di promulgazione
INIZIO_PATTERN = re.compile(
    r"la Costituzione della Repubblica Italiana nel seguente testo:\s*\n*\n",
    re.DOTALL,
)

# ---------------------------------------------------------------------------
# Pulizia wikitext
# ---------------------------------------------------------------------------

# Rimuove template {{...}} su più righe
TEMPLATE_RE = re.compile(r"\{\{[^}]*\}\}", re.DOTALL)
# Rimuove tabelli wiki {| ... |}
TABLE_RE = re.compile(r"\{\|.*?\|\}", re.DOTALL)
# Pulisce link wiki [[...]] in testo semplice
WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
# Sostituisce <br /> con newline
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
# Rimuove tag <ref>...</ref> su più righe
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.DOTALL)
# Rimuove tag HTML residui
HTML_TAG_RE = re.compile(r"<[^>]+>")
# Pulisce spazi multipli
SPACES_RE = re.compile(r"  +")
# Pulisce righe vuote multiple
BLANK_LINES_RE = re.compile(r"\n{3,}")


def scarica_wikitext() -> str:
    """Scarica il wikitext da Wikisource via API action=raw."""
    import urllib.request

    req = urllib.request.Request(
        WIKISOURCE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        },
    )
    logger.info("Scaricamento da Wikisource…")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    logger.info("Scaricati %d byte", len(raw))
    return raw


def estrai_testo(wikitext: str) -> str:
    """Estrae solo il testo costituzionale, saltando template e metadati iniziali."""
    # Cerchiamo la formula di promulgazione
    m = INIZIO_PATTERN.search(wikitext)
    if m:
        inizio = m.end()
        testo = wikitext[inizio:]
    else:
        logger.warning("Formula di promulgazione non trovata — uso tutto dopo la TOC")
        # Fallback: cerca dopo la tabella dei contenuti
        idx = wikitext.find("|}")
        if idx > 0:
            testo = wikitext[idx + 2 :]
        else:
            testo = wikitext

    return testo.strip()


def converti_heading(linea: str) -> str:
    """Converte un heading wikitext in Markdown."""
    for pattern, repl in HEADING_RULES:
        m = pattern.match(linea)
        if m:
            return pattern.sub(repl, linea)
    return linea


def pulisci_testo(testo: str) -> str:
    """Applica tutte le pulizie al testo."""
    # Rimuovi template
    testo = TEMPLATE_RE.sub("", testo)
    # Rimuovi tabelle wiki
    testo = TABLE_RE.sub("", testo)
    # Pulisci link wiki → testo semplice
    testo = WIKI_LINK_RE.sub(r"\1", testo)
    # Sostituisci <br /> con newline
    testo = BR_RE.sub("\n", testo)
    # Rimuovi ref
    testo = REF_RE.sub("", testo)
    # Rimuovi tag HTML residui
    testo = HTML_TAG_RE.sub("", testo)
    # Pulisci spazi
    testo = SPACES_RE.sub(" ", testo)
    # Rimuovi righe vuote all'inizio
    testo = testo.lstrip("\n")
    return testo


def wikitext_to_markdown(wikitext: str) -> str:
    """Converte il wikitext della Costituzione in Markdown."""
    testo = estrai_testo(wikitext)
    testo = pulisci_testo(testo)

    # Elabora linea per linea per convertire heading
    righe = testo.split("\n")
    output: list[str] = []

    for riga in righe:
        riga = riga.strip()
        if not riga:
            output.append("")
            continue

        riga_convertita = converti_heading(riga)
        output.append(riga_convertita)

    # Unisci e normalizza
    md = "\n".join(output)
    md = BLANK_LINES_RE.sub("\n\n", md)
    md = md.strip()

    # Post-pulizia: categorie wiki in fondo
    md = re.sub(r"\nCategoria:.*$", "", md, flags=re.M)
    # Pulisce heading con segni = residui (es. "### = I =")
    md = re.sub(r"^(#{1,4})\s*=\s*(.+?)\s*=\s*$", r"\1 \2", md, flags=re.M)
    # Pulisce heading tipo "### =I =" (senza spazio dopo =)
    md = re.sub(r"^(#{1,4})\s*=\s*(.+?)\s*=\s*$", r"\1 \2", md, flags=re.M)
    # Converte ''testo'' wikitext in *testo* Markdown (italic)
    md = re.sub(r"'''(.*?)'''", r"**\1**", md)  # bold
    md = re.sub(r"''(.*?)''", r"*\1*", md)        # italic

    return md


def scrivi_output(markdown: str, path: Path) -> None:
    """Scrive il file Markdown con frontmatter."""
    content = FRONTMATTER + "\n" + markdown + "\n"
    path.write_text(content, encoding="utf-8")
    logger.info("Scritto %s (%d byte)", path, len(content))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convertitore Wikisource → Costituzione.md"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("Costituzione.md"),
        help="Percorso output (default: Costituzione.md)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Logging verbose"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    wikitext = scarica_wikitext()
    markdown = wikitext_to_markdown(wikitext)
    scrivi_output(markdown, args.output)

    # Statistiche
    n_articoli = len(re.findall(r"^## Art\.", markdown, re.M))
    n_partizioni = len(re.findall(r"^# ", markdown, re.M))
    logger.info(
        "Convertiti %d articoli in %d partizioni",
        n_articoli,
        n_partizioni,
    )


if __name__ == "__main__":
    main()
