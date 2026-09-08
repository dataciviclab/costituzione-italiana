#!/usr/bin/env python3
"""Scarica e processa le Pronunce della Corte Costituzionale (testo integrale).

Estrae da XML: presidente, relatore, redattore, ecli, collegio, testo, dispositivo.

Dataset originali (3 archi temporali):
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenPronunce_1956_1980.zip
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenPronunce_1981_2000.zip
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenPronunce_2001_oggi.zip

Produce data/pronunce.parquet con una riga per pronuncia.
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import re
import tempfile
import urllib.request

import pyarrow as pa
import pyarrow.parquet as pq
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger("importa-pronunce")

BASE_URL = "https://dati.cortecostituzionale.it/opendata/distribuzione"
ARCHIVES = [
    f"{BASE_URL}/CC_OpenPronunce_1956_1980.zip",
    f"{BASE_URL}/CC_OpenPronunce_1981_2000.zip",
    f"{BASE_URL}/CC_OpenPronunce_2001_oggi.zip",
]

FIELDNAMES = [
    "anno_pronuncia",
    "numero_pronuncia",
    "ecli",
    "tipologia_pronuncia",
    "presidente",
    "relatore_pronuncia",
    "redattore_pronuncia",
    "data_decisione",
    "data_deposito",
    "collegio",
    "testo",
    "dispositivo",
]


def _text(elem: ET.Element | None, tag: str) -> str:
    if elem is None:
        return ""
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _download_zip(url: str, dest: Path) -> Path | None:
    fname = dest / os.path.basename(url)
    if fname.exists() and fname.stat().st_size > 1000:
        logger.info(f"Cache: {fname.name}")
        return fname
    logger.info(f"Scaricamento: {url}")
    try:
        urllib.request.urlretrieve(url, fname)
        return fname
    except Exception as e:
        logger.error(f"Fallito download {url}: {e}")
        return None


def _parse_pronunce_xml(xml_data: bytes) -> list[dict]:
    records: list[dict] = []
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        logger.warning(f"Errore parsing XML: {e}")
        return records

    for pronuncia in root.findall(".//pronuncia"):
        pt = pronuncia.find("pronuncia_testata")
        if pt is None:
            continue

        record = {
            "anno_pronuncia": int(_text(pt, "anno_pronuncia")) if _text(pt, "anno_pronuncia").isdigit() else 0,
            "numero_pronuncia": int(_text(pt, "numero_pronuncia")) if _text(pt, "numero_pronuncia").isdigit() else 0,
            "ecli": _text(pt, "ecli"),
            "tipologia_pronuncia": _text(pt, "tipologia_pronuncia"),
            "presidente": _text(pt, "presidente"),
            "relatore_pronuncia": _text(pt, "relatore_pronuncia"),
            "redattore_pronuncia": _text(pt, "redattore_pronuncia"),
            "data_decisione": _text(pt, "data_decisione"),
            "data_deposito": _text(pt, "data_deposito"),
        }

        ptesto = pronuncia.find("pronuncia_testo")
        if ptesto is not None:
            record["collegio"] = _text(ptesto, "collegio")
            record["testo"] = _text(ptesto, "testo")
            record["dispositivo"] = _text(ptesto, "dispositivo")
        else:
            record["collegio"] = ""
            record["testo"] = ""
            record["dispositivo"] = ""

        records.append(record)

    return records


def _stampa_metriche(records: list[dict]):
    total = len(records)
    if total == 0:
        print("Nessun record estratto.")
        return

    from collections import Counter
    anni = Counter(r["anno_pronuncia"] for r in records)
    tipi = Counter(r["tipologia_pronuncia"] for r in records)
    relatori = Counter(r["relatore_pronuncia"] for r in records if r["relatore_pronuncia"])
    con_testo = sum(1 for r in records if r["testo"])
    con_disp = sum(1 for r in records if r["dispositivo"])

    print(f"\n📊 Pronunce — metriche")
    print(f"{'='*40}")
    print(f"  Record:           {total:>8,}")
    print(f"  Con testo:        {con_testo:>8,} ({con_testo/total*100:.1f}%)")
    print(f"  Con dispositivo:  {con_disp:>8,} ({con_disp/total*100:.1f}%)")
    print(f"  Anni: {min(anni.keys())} - {max(anni.keys())}")
    print(f"\n  Top 10 relatori:")
    for r, c in relatori.most_common(10):
        print(f"    {r:40s} {c:>5,}")


def main():
    parser = argparse.ArgumentParser(description="Importa pronunce Corte Costituzionale")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--cache-dir", default="/tmp/cc_pronunce_cache")
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

    zip_paths: list[Path] = []
    for url in ARCHIVES:
        p = _download_zip(url, cachedir)
        if p:
            zip_paths.append(p)

    if not zip_paths:
        logger.error("Nessun archivio scaricato.")
        return

    records: list[dict] = []
    for archive_zip in sorted(zip_paths):
        logger.info(f"\nElaborazione: {archive_zip.name}")
        with zipfile.ZipFile(archive_zip) as zf_outer:
            for inner_name in sorted(zf_outer.namelist()):
                if not inner_name.endswith(".zip"):
                    continue
                inner_data = zf_outer.read(inner_name)
                with zipfile.ZipFile(io.BytesIO(inner_data)) as zf_inner:
                    for xml_name in zf_inner.namelist():
                        if not xml_name.endswith(".xml"):
                            continue
                        xml_data = zf_inner.read(xml_name)
                        recs = _parse_pronunce_xml(xml_data)
                        records.extend(recs)
                        logger.debug(f"  {xml_name}: {len(recs)} record")

    csv_path = outdir / "pronunce.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(records)
    logger.info(f"\nCSV: {csv_path} ({len(records)} righe)")

    pqt = outdir / "pronunce.parquet"
    table = pa.Table.from_pylist(records)
    pq.write_table(table, pqt)
    logger.info(f"Parquet: {pqt} ({table.num_rows} righe)")

    _stampa_metriche(records)


if __name__ == "__main__":
    main()
