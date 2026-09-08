#!/usr/bin/env python3
"""Scarica e processa l'Anagrafica dei Giudici Costituzionali.

Dataset: https://dati.cortecostituzionale.it/opendata/Anagrafica_giudici/Cc_Opendata_AnagraficaGiudici.zip

Produce data/giudici.parquet con una riga per giudice.
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import urllib.request

import pyarrow as pa
import pyarrow.parquet as pq
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger("importa-giudici")

URL = "https://dati.cortecostituzionale.it/opendata/Anagrafica_giudici/Cc_Opendata_AnagraficaGiudici.zip"

FIELDNAMES = [
    "nome_cognome",
    "cognome",
    "nome",
    "titolo",
    "eletto_da",
    "data_nomina",
    "data_giuramento",
    "data_cessazione",
    "nota_biografica",
]


def _text(elem: ET.Element | None, tag: str) -> str:
    if elem is None:
        return ""
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def main():
    parser = argparse.ArgumentParser(description="Importa anagrafica giudici Corte Costituzionale")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--cache-dir", default="/tmp/cc_giudici_cache")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    outdir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent.parent / "data"
    outdir.mkdir(parents=True, exist_ok=True)
    cachedir = Path(args.cache_dir)
    cachedir.mkdir(parents=True, exist_ok=True)

    # Download
    cache_file = cachedir / os.path.basename(URL)
    if not cache_file.exists() or cache_file.stat().st_size < 1000:
        logger.info(f"Scaricamento: {URL}")
        urllib.request.urlretrieve(URL, cache_file)
    else:
        logger.info(f"Cache: {cache_file.name}")

    # Parse
    with zipfile.ZipFile(cache_file) as zf:
        xml_name = [n for n in zf.namelist() if n.endswith(".xml")][0]
        content = zf.read(xml_name)

    root = ET.fromstring(content)
    giudici = root.findall(".//Giudice_costituzionale")

    records = []
    for g in giudici:
        records.append({
            "nome_cognome": _text(g, "Nome_Cognome"),
            "cognome": _text(g, "Cognome"),
            "nome": _text(g, "Nome"),
            "titolo": _text(g, "Titolo"),
            "eletto_da": _text(g, "Eletto_da"),
            "data_nomina": _text(g, "data_nomina"),
            "data_giuramento": _text(g, "data_giuramento"),
            "data_cessazione": _text(g, "data_cessazione"),
            "nota_biografica": _text(g, "Nota_biografica"),
        })

    # CSV
    csv_path = outdir / "giudici.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(records)
    logger.info(f"CSV: {csv_path} ({len(records)} righe)")

    # Parquet
    pqt = outdir / "giudici.parquet"
    table = pa.Table.from_pylist(records)
    pq.write_table(table, pqt)
    logger.info(f"Parquet: {pqt} ({table.num_rows} righe)")

    # Stats
    from collections import Counter
    eletto_da = Counter(r["eletto_da"] for r in records if r["eletto_da"])
    print(f"\n📊 Giudici — metriche")
    print(f"{'='*40}")
    print(f"  Totale: {len(records)}")
    print(f"  Con data_nomina: {sum(1 for r in records if r['data_nomina'])}")
    print(f"  Con eletto_da: {sum(1 for r in records if r['eletto_da'])}")
    print(f"\n  Distribuzione eletto_da:")
    for k, v in eletto_da.most_common():
        print(f"    {k:35s} {v:>3}")


if __name__ == "__main__":
    main()
