#!/usr/bin/env python3
"""Importa le citazioni della Costituzione nella legislazione ordinaria.

Scarica il dataset citazioni-costituzionali.parquet da italia-corpus (GitHub)
e lo salva in data/ con arricchimento: testo dell'articolo citato.

Fonte: data/derived/citazioni-costituzionali.parquet in
       https://github.com/dataciviclab/italia-corpus

Produce data/citazioni-legislative.parquet.

Uso:
    python3 strumenti/importa-citazioni-da-italia-corpus.py
"""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path
from urllib.request import urlopen

logger = logging.getLogger("importa-citazioni")

# URL del dataset in italia-corpus (repo pubblico)
PARQUET_URL = (
    "https://raw.githubusercontent.com/dataciviclab/italia-corpus/main/"
    "data/derived/citazioni-costituzionali.parquet"
)


def _scarica_parquet(url: str) -> bytes:
    """Scarica un parquet da URL."""
    logger.info("Download %s", url)
    with urlopen(url, timeout=60) as resp:
        return resp.read()


def _carica_articoli(data_dir: Path) -> dict[int, str]:
    """Carica articoli.parquet per arricchire con testo."""
    pqt = data_dir / "articoli.parquet"
    if not pqt.exists():
        logger.warning("articoli.parquet non trovato, arricchimento saltato")
        return {}
    import pyarrow.parquet as pq

    t = pq.read_table(pqt)
    result: dict[int, str] = {}
    for i in range(t.num_rows):
        a = t.column("articolo")[i].as_py()
        testo = t.column("testo")[i].as_py()
        if a is not None and testo:
            result[a] = testo[:300]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=None, help="Directory output (default: data/)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.output_dir:
        outdir = Path(args.output_dir)
    else:
        outdir = Path(__file__).resolve().parent.parent / "data"
    outdir.mkdir(parents=True, exist_ok=True)

    # Scarica il parquet da italia-corpus
    raw = _scarica_parquet(PARQUET_URL)

    import io
    import pyarrow.parquet as pq

    table = pq.read_table(io.BytesIO(raw))

    # Arricchisci con testo articolo
    articoli = _carica_articoli(outdir)
    if articoli:
        testi = []
        for art in table.column("articolo").to_pylist():
            testi.append(articoli.get(art, ""))
        import pyarrow as pa

        table = table.append_column(
            "articolo_testo", pa.array(testi, type=pa.string())
        )

    # Salva CSV
    csv_path = outdir / "citazioni-legislative.csv"
    pqt_path = outdir / "citazioni-legislative.parquet"

    fieldnames = [
        "fonte_filename",
        "fonte_collezione",
        "fonte_anno",
        "fonte_tipo",
        "articolo",
        "contesto",
    ]
    if articoli:
        fieldnames.append("articolo_testo")

    cols = [table.column(f) for f in fieldnames]
    import pyarrow as pa

    out_table = pa.table({f: c for f, c in zip(fieldnames, cols)})
    pq.write_table(out_table, pqt_path)
    logger.info(f"Parquet: {pqt_path} ({out_table.num_rows} righe, {out_table.num_columns} colonne)")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        rows = []
        for i in range(out_table.num_rows):
            rows.append({f: out_table.column(f)[i].as_py() for f in fieldnames})
        w.writerows(rows)
    logger.info(f"CSV: {csv_path} ({len(rows)} righe)")


if __name__ == "__main__":
    main()
