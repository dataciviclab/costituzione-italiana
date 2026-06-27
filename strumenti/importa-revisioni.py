#!/usr/bin/env python3
"""Importa le leggi di revisione costituzionale da italia-corpus.

Legge tutti i file Markdown da italia-corpus/Leggi costituzionali/,
estrae il frontmatter e gli articoli della Costituzione modificati
(dai link a #art_N nel testo), e produce data/revisioni.csv e .parquet.

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
    Path(__file__).resolve().parent.parent.parent / "italia-corpus"
    / "Leggi costituzionali"
)

# Pattern per estrarre articoli della Costituzione dal testo
# Cattura link come: [articolo 9 della Costituzione](...#art_9)
# o: [articolo 41 della Costituzione](...#art_41)
# o: [articoli 56, 57 e 59 della Costituzione](...#art_56) (nel testo)
# Pattern: [articolo N della Costituzione], [art. N della Costituzione], 
# [dell'articolo N della Costituzione], [articoli N, M e O della Costituzione]
ART_COST_RE = re.compile(
    r"\[(?:dell['\u2019])?(?:articol[oi]|art\.?)\s+(\d+(?:,\s*\d+)*(?:\s+e\s+\d+)*)"
    r"\s+della\s+Costituzione\]",
    re.IGNORECASE,
)

# Pattern per "articoli N, M e O" — estrae numeri singoli
NUM_RE = re.compile(r"\d+")


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


def estrai_articoli_dal_testo(testo: str) -> list[int]:
    """Estrae i numeri degli articoli della Costituzione menzionati nel testo."""
    articoli: set[int] = set()
    for m in ART_COST_RE.finditer(testo):
        numeri_testo = m.group(1)
        for n in NUM_RE.findall(numeri_testo):
            articoli.add(int(n))
    return sorted(articoli)


def importa_revisioni(corpus_dir: Path) -> list[dict]:
    """Importa tutte le leggi di revisione dal corpus."""
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

        articoli = estrai_articoli_dal_testo(text)
        titolo = meta.get("titolo", fpath.stem)

        rev = {
            "urn": meta.get("urn", ""),
            "codice_redazionale": meta.get("codice_redazionale", ""),
            "data": meta.get("data", ""),
            "titolo": titolo,
            "articoli_modificati": articoli,
            "n_articoli": len(articoli),
            "tipo": "statuto_speciale" if "Statuto speciale" in titolo or "statuto speciale" in titolo
                   else "modifica_costituzione" if articoli
                   else "altra_legge_costituzionale",
        }
        revisioni.append(rev)

    return revisioni


def scrivi_csv(revisioni: list[dict], path: Path) -> None:
    """Scrive il CSV."""
    campi = ["urn", "codice_redazionale", "data", "titolo",
             "articoli_modificati", "n_articoli", "tipo"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for rev in revisioni:
            row = {k: rev.get(k, "") for k in campi}
            # serializza lista come stringa
            if isinstance(row["articoli_modificati"], list):
                row["articoli_modificati"] = ", ".join(str(a) for a in row["articoli_modificati"])
            w.writerow(row)
    logger.info("Scritto %s con %d righe", path, len(revisioni))


def scrivi_parquet(revisioni: list[dict], path: Path) -> None:
    """Scrive il parquet."""
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa leggi di revisione costituzionale da italia-corpus"
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=DEFAULT_CORPUS,
        help="Percorso a italia-corpus/Leggi costituzionali/",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("data"),
        help="Directory output (default: data/)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Livello di logging",
    )
    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    revisioni = importa_revisioni(args.corpus_dir)
    if not revisioni:
        logger.error("Nessuna revisione importata")
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = args.output_dir / "revisioni.csv"
    scrivi_csv(revisioni, csv_path)

    parquet_path = args.output_dir / "revisioni.parquet"
    scrivi_parquet(revisioni, parquet_path)

    # Statistiche
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
