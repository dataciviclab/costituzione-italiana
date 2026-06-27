#!/usr/bin/env python3
"""Importa le leggi di revisione costituzionale da italia-corpus.

Estrae gli articoli della Costituzione modificati direttamente dal titolo
della legge (pattern: "Modifica all'articolo N", "Modifiche agli articoli N, M",
"Modifiche al titolo V della parte seconda", …).

Produce data/revisioni.csv e .parquet.

Uso:
    python3 strumenti/importa-revisioni.py [--corpus-dir DIR] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger("importa-revisioni")

# Dove cercare italia-corpus
DEFAULT_CORPUS = (
    Path(__file__).resolve().parent.parent.parent
    / "italia-corpus"
    / "Leggi costituzionali"
)

# ---------------------------------------------------------------------------
# Pattern per estrarre articoli modificati dal TITOLO
# ---------------------------------------------------------------------------

# "Modifica all'articolo 27 della Costituzione"
# "Modifica dell'articolo 51 della Costituzione"
RE_MODIFICA_UNO = re.compile(
    r"l['\u2019]articolo\s+(\d+)\s+della\s+Costituzione",
    re.IGNORECASE,
)

# "Modifiche agli articoli 56, 57 e 59 della Costituzione"
# "Modificazioni agli articoli 56, 57 e 60 della Costituzione"
# "Modifiche degli articoli 96, 134 e 135 della Costituzione"
# "Modificazione dell'articolo 135 della Costituzione"
RE_MODIFICA_PIU = re.compile(
    r"(?:Modifica|Modifiche|Modificazioni|Modificazione)\s+"
    r"(?:all['\u2019]|degli|agli)\s+articol[oi]\s+"
    r"((?:\d+(?:,\s*|\s+e\s+)*)+)",
    re.IGNORECASE,
)

# "Modifiche al titolo V della parte seconda della Costituzione"
RE_TITOLO_V = re.compile(
    r"Modifiche\s+al\s+titolo\s+([VX]+)\s+della\s+parte\s+seconda",
    re.IGNORECASE,
)

# "Modifica dell'articolo 88, secondo comma, della Costituzione"
RE_ART_VIRGOLA = re.compile(
    r"Modifica\s+dell['\u2019]articolo\s+(\d+)",
    re.IGNORECASE,
)

# "Revisione dell'articolo 79 della Costituzione"
RE_REVISIONE = re.compile(
    r"Revisione\s+dell['\u2019]articolo\s+(\d+)",
    re.IGNORECASE,
)

NUM_RE = re.compile(r"\d+")

# ---------------------------------------------------------------------------
# Mappa: Titolo → articoli (casi speciali)
# ---------------------------------------------------------------------------

# Le leggi che modificano interi titoli della Costituzione
TITOLO_MAP: dict[str, list[int]] = {
    "V": list(range(114, 133 + 1)),  # Titolo V: Regioni, Province, Comuni
}


def _numeri(testo: str) -> list[int]:
    return [int(n) for n in NUM_RE.findall(testo)]


def _estrai_dal_titolo(titolo: str) -> list[int]:
    """Estrae gli articoli modificati dal titolo della legge."""
    # Pattern 1: "Modifiche agli articoli N, M e O della Costituzione"
    m = RE_MODIFICA_PIU.search(titolo)
    if m:
        return _numeri(m.group(1))

    # Pattern 2: "Modifica all'articolo N della Costituzione"
    m = RE_MODIFICA_UNO.search(titolo)
    if m:
        return [int(m.group(1))]

    # Pattern 3: "Modifica dell'articolo N, ... della Costituzione"
    m = RE_ART_VIRGOLA.search(titolo)
    if m:
        return [int(m.group(1))]

    # Pattern 4: "Revisione dell'articolo N della Costituzione"
    m = RE_REVISIONE.search(titolo)
    if m:
        return [int(m.group(1))]

    # Pattern 5: "Modifiche al titolo V della parte seconda"
    m = RE_TITOLO_V.search(titolo)
    if m:
        return TITOLO_MAP.get(m.group(1), [])

    return []


# ---------------------------------------------------------------------------
# Classificazione
# ---------------------------------------------------------------------------


def _classifica(titolo: str, articoli_modificati: list[int]) -> str:
    """Classifica il tipo di legge costituzionale."""

    # Statuti speciali
    statuto_patterns = [
        r"Statuto\s+speciale",
        r"Statuto\s+della\s+Regione\s+siciliana",
        r"Conversione in legge costituzionale dello Statuto",
        r"statut[oi]\s+speciali",
        r"Statuto speciale per la",
    ]
    for pat in statuto_patterns:
        if re.search(pat, titolo, re.IGNORECASE):
            return "statuto_speciale"

    # Referendum / proroghe / norme integrative → altre
    altre_patterns = [
        "referendum", "Proroga del termine", "Cessazione degli effetti",
        "Soppressione del Senato", "Scadenza del termine",
        "Norme integrative", "Norme sui giudizi",
        "Istituzione di una Commissione", "Funzioni della Commissione",
        "Assegnazione di tre Senatori", "Indizione di un",
        "Modifica del termine", "Modifiche ed integrazioni alla legge costituzionale",
    ]
    for pat in altre_patterns:
        if pat.lower() in titolo.lower():
            return "altra_legge_costituzionale"

    # Modifiche a statuti speciali (es. modifiche a uno statuto speciale)
    if re.search(r"dello\s+Statuto\s+(?:speciale\s+)?(?:della\s+)?Regione", titolo, re.IGNORECASE):
        return "statuto_speciale"

    if re.search(r"Modifica\s+dell['\u2019]articolo\s+\d+\s+dello\s+Statuto", titolo, re.IGNORECASE):
        return "statuto_speciale"

    if articoli_modificati:
        return "modifica_costituzione"

    return "altra_legge_costituzionale"


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parsa YAML frontmatter semplice (--- ... ---)."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    result: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def scrivi_csv(revisioni: list[dict], path: Path) -> None:
    campi = [
        "urn", "codice_redazionale", "data", "titolo",
        "articoli_modificati", "n_articoli", "tipo",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for rev in revisioni:
            row = {k: rev.get(k, "") for k in campi}
            if isinstance(row["articoli_modificati"], list):
                row["articoli_modificati"] = ", ".join(str(a) for a in row["articoli_modificati"])
            w.writerow(row)
    logger.info("Scritto %s con %d righe", path, len(revisioni))


def scrivi_parquet(revisioni: list[dict], path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table(
        {
            "urn": [r.get("urn", "") for r in revisioni],
            "codice_redazionale": [r.get("codice_redazionale", "") for r in revisioni],
            "data": [r.get("data", "") for r in revisioni],
            "titolo": [r.get("titolo", "") for r in revisioni],
            "articoli_modificati": [r.get("articoli_modificati", []) for r in revisioni],
            "n_articoli": [r.get("n_articoli", 0) for r in revisioni],
            "tipo": [r.get("tipo", "") for r in revisioni],
        }
    )
    pq.write_table(table, str(path))
    logger.info("Scritto %s", path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def importa_revisioni(corpus_dir: Path) -> list[dict]:
    if not corpus_dir.exists():
        logger.error("Directory non trovata: %s", corpus_dir)
        logger.error("Assicurati che italia-corpus sia clonato nel workspace")
        return []

    md_files = sorted(corpus_dir.glob("*.md"))
    logger.info("Trovati %d file in %s", len(md_files), corpus_dir)

    revisioni: list[dict] = []

    for fpath in md_files:
        text = fpath.read_text("utf-8")
        meta = parse_frontmatter(text)
        titolo = meta.get("titolo", fpath.stem)

        articoli = _estrai_dal_titolo(titolo)
        tipo = _classifica(titolo, articoli)

        revisioni.append(
            {
                "urn": meta.get("urn", ""),
                "codice_redazionale": meta.get("codice_redazionale", ""),
                "data": meta.get("data", ""),
                "titolo": titolo,
                "articoli_modificati": articoli,
                "n_articoli": len(articoli),
                "tipo": tipo,
            }
        )

    return revisioni


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa leggi di revisione costituzionale da italia-corpus"
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=DEFAULT_CORPUS,
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("data"),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    revisioni = importa_revisioni(args.corpus_dir)
    if not revisioni:
        logger.error("Nessuna revisione importata")
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    scrivi_csv(revisioni, args.output_dir / "revisioni.csv")
    scrivi_parquet(revisioni, args.output_dir / "revisioni.parquet")

    n_mod = sum(1 for r in revisioni if r["tipo"] == "modifica_costituzione")
    n_stat = sum(1 for r in revisioni if r["tipo"] == "statuto_speciale")
    n_altre = sum(1 for r in revisioni if r["tipo"] == "altra_legge_costituzionale")
    tot_art = sum(r["n_articoli"] for r in revisioni)
    logger.info(
        "Importate %d leggi: %d modifiche Costituzione, %d statuti speciali, %d altre",
        len(revisioni), n_mod, n_stat, n_altre,
    )
    logger.info("Totale riferimenti ad articoli: %d", tot_art)


if __name__ == "__main__":
    main()
