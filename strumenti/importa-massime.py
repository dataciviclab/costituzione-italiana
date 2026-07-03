#!/usr/bin/env python3
"""Scarica e processa le Massime della Corte Costituzionale.

Le massime sono riassunti strutturati delle pronunce, con esito,
parametri costituzionali evocati e norme impugnate in formato XML
molto più gestibile del testo libero delle pronunce.

Dataset originali (3 archi temporali):
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenMassime_1956_1980.zip
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenMassime_1981_2000.zip
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenMassime_2001_oggi.zip

Produce data/massime.parquet con una riga per massima (flatten).
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
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger("importa-massime")

BASE_URL = "https://dati.cortecostituzionale.it/opendata/distribuzione"
ARCHIVES = [
    f"{BASE_URL}/CC_OpenMassime_1956_1980.zip",
    f"{BASE_URL}/CC_OpenMassime_1981_2000.zip",
    f"{BASE_URL}/CC_OpenMassime_2001_oggi.zip",
]

FIELDNAMES = [
    "id_massima",
    "anno_pronuncia",
    "numero_pronuncia",
    "tipologia_pronuncia",
    "data_decisione",
    "data_deposito",
    "esito",
    "parametro_codice",
    "parametro_descrizione",
    "parametro_articolo",
    "parametro_comma",
    "norma_codice",
    "norma_descrizione",
    "norma_numero",
    "norma_data",
    "norma_articolo",
    "norma_specificazione_articolo",
    "norma_comma",
    "norma_specificazione_comma",
]

# Regex per estrarre esito dal testo della massima
# L'ordine è importante: pattern più specifici prima
RE_ESITO = re.compile(
    r"(?:"
    r"dichiar[ato]*(?:\s+costituzionalmente)?\s+(?:l[']?)illegittimit[àa]\s+costituzionale"
    r"|costituzionalmente\s+illegittim"
    r")",
    re.IGNORECASE,
)
RE_NON_FONDATA = re.compile(
    r"(?:(?:è|sono)\s+dichiarat[aeo]?\s+)?(?:non\s+fondat)",
    re.IGNORECASE,
)
RE_INAMMISSIBILE = re.compile(
    r"(?:(?:è|sono)\s+dichiarat[aeo]?\s+)?inammissibil",
    re.IGNORECASE,
)
RE_MANIFESTA = re.compile(
    r"manifestament",
    re.IGNORECASE,
)


def _classify_esito(testo: str) -> str:
    """Classifica l'esito di una massima basandosi sul testo.

    Returns: illegittimo | non_fondata | inammissibile | misto | altro
    """
    if not testo:
        return "altro"

    flags = set()
    if RE_ESITO.search(testo):
        flags.add("illegittimo")
    if RE_NON_FONDATA.search(testo):
        flags.add("non_fondata")
    if RE_INAMMISSIBILE.search(testo):
        flags.add("inammissibile")
    if RE_MANIFESTA.search(testo):
        flags.add("manifestamente_infondata")

    if len(flags) == 1:
        return flags.pop()
    elif len(flags) > 1:
        return "misto"
    return "altro"


def _download_zip(url: str, dest: Path) -> Path | None:
    """Scarica un archivio ZIP se non già presente in cache."""
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


def _parse_massime_xml(xml_data: bytes) -> list[dict]:
    """Parsa un XML annuale di massime e restituisce lista di record."""
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

        anno = pt.findtext("anno_pronuncia", "")
        numero = pt.findtext("numero_pronuncia", "")
        tipologia = pt.findtext("tipologia_pronuncia", "")
        data_dec = pt.findtext("data_decisione", "")
        data_dep = pt.findtext("data_deposito", "")

        # Calcola esito aggregato per questa pronuncia
        massime_testi: list[str] = []
        for massima in pronuncia.findall(".//massima"):
            t = massima.findtext("testo", "")
            if t:
                massime_testi.append(t)

        esito_pronuncia = "altro"
        if massime_testi:
            # Unisci tutti i testi delle massime per determinare l'esito
            testo_completo = " ".join(massime_testi)
            esito_pronuncia = _classify_esito(testo_completo)

        for massima in pronuncia.findall(".//massima"):
            num_massima = massima.findtext("numero", "")

            # Normalizza id_massima a int (vuoto → 0)
            try:
                num_massima_int = int(num_massima) if num_massima else 0
            except ValueError:
                num_massima_int = 0

            for parametro in massima.findall(".//parametri/parametro"):
                for norma in massima.findall(".//norme/norma"):
                    record = {
                        "id_massima": num_massima_int,
                        "anno_pronuncia": int(anno) if anno.isdigit() else 0,
                        "numero_pronuncia": int(numero) if numero.isdigit() else 0,
                        "tipologia_pronuncia": tipologia,
                        "data_decisione": data_dec,
                        "data_deposito": data_dep,
                        "esito": esito_pronuncia,
                        "parametro_codice": parametro.findtext("codice", ""),
                        "parametro_descrizione": parametro.findtext("descrizione", ""),
                        "parametro_articolo": parametro.findtext("articolo", ""),
                        "parametro_comma": parametro.findtext("comma", ""),
                        "norma_codice": norma.findtext("codice", ""),
                        "norma_descrizione": norma.findtext("descrizione", ""),
                        "norma_numero": norma.findtext("numero", ""),
                        "norma_data": norma.findtext("data", ""),
                        "norma_articolo": norma.findtext("articolo", ""),
                        "norma_specificazione_articolo": norma.findtext("specificazione_articolo", ""),
                        "norma_comma": norma.findtext("comma", ""),
                        "norma_specificazione_comma": norma.findtext("specificazione_comma", ""),
                    }
                    records.append(record)

            # Massime senza parametri/norme (es. massime di principio)
            if not list(massima.findall(".//parametri/parametro")) and not list(massima.findall(".//norme/norma")):
                record = {
                    "id_massima": num_massima_int,
                    "anno_pronuncia": int(anno) if anno.isdigit() else 0,
                    "numero_pronuncia": int(numero) if numero.isdigit() else 0,
                    "tipologia_pronuncia": tipologia,
                    "data_decisione": data_dec,
                    "data_deposito": data_dep,
                    "esito": esito_pronuncia,
                    "parametro_codice": "",
                    "parametro_descrizione": "",
                    "parametro_articolo": "",
                    "parametro_comma": "",
                    "norma_codice": "",
                    "norma_descrizione": "",
                    "norma_numero": "",
                    "norma_data": "",
                    "norma_articolo": "",
                    "norma_specificazione_articolo": "",
                    "norma_comma": "",
                    "norma_specificazione_comma": "",
                }
                records.append(record)

    return records


def _stampa_metriche(records: list[dict]):
    """Stampa metriche riassuntive."""
    total = len(records)
    if total == 0:
        print("Nessun record estratto.")
        return

    esiti = Counter(r["esito"] for r in records)
    pronunce = len({(r["anno_pronuncia"], r["numero_pronuncia"]) for r in records})
    massime_univoche = len({r["id_massima"] for r in records})
    con_esito = sum(1 for r in records if r["esito"] != "altro")

    print(f"\n📊 Massime — metriche")
    print(f"{'='*40}")
    print(f"  Record (parametri×norme): {total:>8,}")
    print(f"  Pronunce coperte:         {pronunce:>8,}")
    print(f"  Massime univoche:         {massime_univoche:>8,}")
    print(f"  Con esito determinato:    {con_esito:>8,} ({con_esito/total*100:.1f}%)")
    print(f"\n  Distribuzione esiti:")
    for k, v in esiti.most_common():
        print(f"    {k:30s} {v:>6,} ({v/total*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Importa massime Corte Costituzionale")
    parser.add_argument("--output-dir", default=None, help="Directory output (default: data/)")
    parser.add_argument("--cache-dir", default="/tmp/cc_massime_cache", help="Directory cache ZIP")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging verbose")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    # Determina directory output
    if args.output_dir:
        outdir = Path(args.output_dir)
    else:
        outdir = Path(__file__).resolve().parent.parent / "data"
    outdir.mkdir(parents=True, exist_ok=True)

    cachedir = Path(args.cache_dir)
    cachedir.mkdir(parents=True, exist_ok=True)

    # Scarica archivi
    zip_paths: list[Path] = []
    for url in ARCHIVES:
        p = _download_zip(url, cachedir)
        if p:
            zip_paths.append(p)

    if not zip_paths:
        logger.error("Nessun archivio scaricato.")
        return

    # Parsa tutti gli XML
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
                        recs = _parse_massime_xml(xml_data)
                        records.extend(recs)
                        year = re.search(r"(\d{4})", xml_name)
                        anno = year.group(1) if year else "??"
                        logger.debug(f"  {xml_name}: {len(recs)} record")

    # Salva CSV
    csv_path = outdir / "massime.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(records)
    logger.info(f"\nCSV: {csv_path} ({len(records)} righe)")

    # Salva Parquet
    pqt = outdir / "massime.parquet"
    table = pa.Table.from_pylist(records)
    pq.write_table(table, pqt)
    logger.info(f"Parquet: {pqt} ({table.num_rows} righe, {table.num_columns} colonne)")

    _stampa_metriche(records)


if __name__ == "__main__":
    main()
