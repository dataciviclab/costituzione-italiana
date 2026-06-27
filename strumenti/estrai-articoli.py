#!/usr/bin/env python3
"""Estrae articoli da Costituzione.md e produce data/articoli.csv e .parquet.

Uso:
    python3 strumenti/estrai-articoli.py [--input INPUT] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger("estrai-articoli")

# Pattern per riconoscere gli heading nel Markdown
RE_ARTICOLO = re.compile(r"^## Art\.\s*(\d+[bis]?)$")
RE_DISPOSIZIONE = re.compile(r"^###\s*([IVXLCDM]+)$")
RE_PARTE = re.compile(r"^#\s+(.+)$")
RE_TITOLO = re.compile(r"^##\s+(.+)$")
RE_SEZIONE = re.compile(r"^###\s+(.+)$")


def parse_costituzione(md: str) -> list[dict]:
    """Parsa il Markdown della Costituzione e restituisce lista di articoli."""
    righe = md.split("\n")

    articoli: list[dict] = []
    parte_attuale = ""
    titolo_attuale = ""
    sezione_attuale = ""
    articolo_corrente: dict | None = None
    testo_accumulato: list[str] = []

    def finalizza_articolo() -> None:
        """Salva l'articolo corrente se esiste."""
        nonlocal articolo_corrente, testo_accumulato
        if articolo_corrente is not None:
            testo = "\n".join(testo_accumulato).strip()
            commi = max(1, testo.count("\n\n") + 1) if testo else 0
            articolo_corrente["testo"] = testo
            articolo_corrente["commi"] = commi
            articoli.append(articolo_corrente)
            articolo_corrente = None
            testo_accumulato = []

    for riga in righe:
        # Salta frontmatter
        if riga.startswith("---"):
            continue
        if riga.startswith("tipo:") or riga.startswith("numero:") or riga.startswith("data:"):
            continue
        if riga.startswith("titolo:") or riga.startswith("urn:") or riga.startswith("codice_redazionale:"):
            continue
        if riga.startswith("vigente:") or riga.startswith("fonte:") or riga.startswith("licenza:"):
            continue

        # Controlla se è un heading di parte
        m_parte = RE_PARTE.match(riga)
        if m_parte and "Art." not in riga and "Disposizioni" not in riga:
            finalizza_articolo()
            parte_attuale = m_parte.group(1)
            titolo_attuale = ""
            sezione_attuale = ""
            continue

        # Controlla se è "Disposizioni transitorie e finali"
        if riga.startswith("# Disposizioni"):
            finalizza_articolo()
            parte_attuale = "Disposizioni transitorie e finali"
            titolo_attuale = ""
            sezione_attuale = ""
            continue

        # Controlla se è un titolo
        m_titolo = RE_TITOLO.match(riga)
        if m_titolo and "Art." not in riga:
            finalizza_articolo()
            titolo_attuale = m_titolo.group(1)
            sezione_attuale = ""
            continue

        # Controlla se è una sezione (###) ma non una disposizione transitoria (### I)
        m_sezione = RE_SEZIONE.match(riga)
        if m_sezione and "Art." not in riga:
            # Potrebbe essere una sezione o una disposizione transitoria
            testo_sez = m_sezione.group(1)
            # Se sembra un numero romano, è una disposizione transitoria
            if re.match(r"^[IVXLCDM]+$", testo_sez):
                finalizza_articolo()
                articolo_corrente = {
                    "articolo": None,
                    "disposizione": testo_sez,
                    "parte": parte_attuale,
                    "titolo": titolo_attuale,
                    "sezione": sezione_attuale,
                    "heading": f"Disposizione transitoria {testo_sez}",
                }
                testo_accumulato = []
                continue
            else:
                finalizza_articolo()
                sezione_attuale = testo_sez
                continue

        # Controlla se è un articolo
        m_art = RE_ARTICOLO.match(riga)
        if m_art:
            finalizza_articolo()
            num = m_art.group(1)
            articolo_corrente = {
                "articolo": num,
                "disposizione": None,
                "parte": parte_attuale,
                "titolo": titolo_attuale,
                "sezione": sezione_attuale,
                "heading": f"Art. {num}",
            }
            testo_accumulato = []
            continue

        # Accumula testo per l'articolo corrente
        if articolo_corrente is not None:
            # Salta righe vuote all'inizio
            if not riga.strip() and not testo_accumulato:
                continue
            testo_accumulato.append(riga)

    # Finalizza l'ultimo articolo
    finalizza_articolo()

    return articoli


def scrivi_csv(articoli: list[dict], path: Path) -> None:
    """Scrive il CSV."""
    campi = ["articolo", "disposizione", "parte", "titolo", "sezione", "heading", "testo", "commi"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for art in articoli:
            row = {k: art.get(k, "") for k in campi}
            w.writerow(row)
    logger.info("Scritto %s con %d righe", path, len(articoli))


def scrivi_parquet(articoli: list[dict], path: Path) -> None:
    """Scrive il parquet."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    # Converte articolo in intero dove possibile
    def articolo_int(v: str | None) -> int | None:
        if v is None:
            return None
        try:
            # Rimuovi suffisso "bis" se presente
            return int(v) if v.isdigit() else None
        except (ValueError, TypeError):
            return None

    table = pa.table(
        {
            "articolo": [articolo_int(a.get("articolo")) for a in articoli],
            "disposizione": [a.get("disposizione") for a in articoli],
            "parte": [a.get("parte", "") for a in articoli],
            "titolo": [a.get("titolo", "") for a in articoli],
            "sezione": [a.get("sezione", "") for a in articoli],
            "heading": [a.get("heading", "") for a in articoli],
            "testo": [a.get("testo", "") for a in articoli],
            "commi": [a.get("commi", 0) for a in articoli],
        }
    )
    pq.write_table(table, str(path))
    logger.info("Scritto %s", path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estrae articoli da Costituzione.md"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("Costituzione.md"),
        help="Percorso input (default: Costituzione.md)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("data"),
        help="Directory output (default: data/)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    if not args.input.exists():
        logger.error("File non trovato: %s", args.input)
        sys.exit(1)

    md = args.input.read_text(encoding="utf-8")
    articoli = parse_costituzione(md)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = args.output_dir / "articoli.csv"
    scrivi_csv(articoli, csv_path)

    parquet_path = args.output_dir / "articoli.parquet"
    scrivi_parquet(articoli, parquet_path)

    logger.info(
        "Estratti %d articoli/disposizioni, %d commi totali",
        len(articoli),
        sum(a.get("commi", 0) for a in articoli),
    )


if __name__ == "__main__":
    main()
