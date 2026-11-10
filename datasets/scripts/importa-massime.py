#!/usr/bin/env python3
"""Scarica e processa le Massime della Corte Costituzionale.

Le massime sono riassunti strutturati delle pronunce, con esito,
parametri costituzionali evocati e norme impugnate.

Dataset originali (3 archi temporali):
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenMassime_1956_1980.zip
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenMassime_1981_2000.zip
  https://dati.cortecostituzionale.it/opendata/distribuzione/CC_OpenMassime_2001_oggi.zip

Produce data/massime.parquet con **una riga per massima** (46.665 record).
I parametri costituzionali e le norme impugnate sono due liste indipendenti
della stessa massima: restano JSON nel clean e vengono esplose nei mart
(`mart_massime_parametri`, `mart_massime_norme`). Il vecchio parser faceva
il prodotto cartesiano delle due liste: 267k righe inventate e 6.276 massime
perse (quelle con una sola delle due liste).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import re
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

import pyarrow as pa
import pyarrow.parquet as pq

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
    "tipologia_giudizio",
    "data_decisione",
    "data_deposito",
    "esito",
    "titolo",
    "testo",
    "parametri",
    "norme",
    "n_parametri",
    "n_norme",
]

PARAMETRO_FIELDS = (
    "codice",
    "descrizione",
    "numero",
    "data",
    "articolo",
    "specificazione_articolo",
    "comma",
    "specificazione_comma",
)
NORMA_FIELDS = PARAMETRO_FIELDS

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


def _text(elem: ET.Element | None, tag: str) -> str:
    if elem is None:
        return ""
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _fields(elem: ET.Element, fieldnames: tuple[str, ...]) -> dict[str, str]:
    """Estrae i campi figli di un elemento (parametro o norma)."""
    return {name: _text(elem, name) for name in fieldnames}


def _load_zip(url: str, dest: Path) -> Path | None:
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
    """Parsa un XML annuale di massime: una riga per massima.

    `parametri` e `norme` sono liste indipendenti della massima: vengono
    serializzate in JSON, mai moltiplicate tra loro.
    """
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

        massime = pronuncia.findall(".//massima")
        testi = [m.findtext("testo", "") for m in massime if m.findtext("testo", "")]
        esito = _classify_esito(" ".join(testi))

        for massima in massime:
            parametri_el = massima.find("parametri")
            norme_el = massima.find("norme")
            parametri = (
                [_fields(p, PARAMETRO_FIELDS) for p in parametri_el.findall("parametro")]
                if parametri_el is not None
                else []
            )
            norme = (
                [_fields(n, NORMA_FIELDS) for n in norme_el.findall("norma")]
                if norme_el is not None
                else []
            )

            num_massima = massima.findtext("numero", "")
            records.append(
                {
                    "id_massima": int(num_massima) if num_massima.isdigit() else 0,
                    "anno_pronuncia": int(anno) if anno.isdigit() else 0,
                    "numero_pronuncia": int(numero) if numero.isdigit() else 0,
                    "tipologia_pronuncia": pt.findtext("tipologia_pronuncia", ""),
                    "tipologia_giudizio": pt.findtext("tipologia_giudizio", ""),
                    "data_decisione": pt.findtext("data_decisione", ""),
                    "data_deposito": pt.findtext("data_deposito", ""),
                    "esito": esito,
                    "titolo": massima.findtext("titolo", ""),
                    "testo": massima.findtext("testo", ""),
                    "parametri": json.dumps(parametri, ensure_ascii=False),
                    "norme": json.dumps(norme, ensure_ascii=False),
                    "n_parametri": len(parametri),
                    "n_norme": len(norme),
                }
            )

    return records


def _stampa_metriche(records: list[dict]) -> None:
    """Stampa metriche riassuntive."""
    total = len(records)
    if total == 0:
        print("Nessun record estratto.")
        return

    esiti = Counter(r["esito"] for r in records)
    pronunce = len({(r["anno_pronuncia"], r["numero_pronuncia"]) for r in records})
    con_esito = sum(1 for r in records if r["esito"] != "altro")
    con_titolo = sum(1 for r in records if r.get("titolo"))
    con_testo = sum(1 for r in records if r.get("testo"))
    n_parametri = sum(r["n_parametri"] for r in records)
    n_norme = sum(r["n_norme"] for r in records)

    tipi_giudizio = Counter(
        r["tipologia_giudizio"] for r in records if r.get("tipologia_giudizio")
    )

    print("\n📊 Massime — metriche")
    print(f"{'='*40}")
    print(f"  Massime:                  {total:>8,}")
    print(f"  Pronunce coperte:         {pronunce:>8,}")
    print(f"  Parametri:                {n_parametri:>8,}")
    print(f"  Norme:                    {n_norme:>8,}")
    print(f"  Con esito determinato:    {con_esito:>8,} ({con_esito/total*100:.1f}%)")
    print(f"  Con titolo:               {con_titolo:>8,} ({con_titolo/total*100:.1f}%)")
    print(f"  Con testo:                {con_testo:>8,} ({con_testo/total*100:.1f}%)")
    print("\n  Distribuzione esiti:")
    for k, v in esiti.most_common():
        print(f"    {k:30s} {v:>6,} ({v/total*100:.1f}%)")
    if tipi_giudizio:
        print("\n  Distribuzione tipologia giudizio:")
        for k, v in tipi_giudizio.most_common():
            print(f"    {k:60s} {v:>6,} ({v/total*100:.1f}%)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa massime Corte Costituzionale")
    parser.add_argument("--output-dir", default=None, help="Directory output (default: data/)")
    parser.add_argument("--cache-dir", default="/tmp/cc_massime_cache", help="Directory cache ZIP")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging verbose")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if args.output_dir:
        outdir = Path(args.output_dir)
    else:
        outdir = Path(__file__).resolve().parent.parent / "data"
    outdir.mkdir(parents=True, exist_ok=True)

    cachedir = Path(args.cache_dir)
    cachedir.mkdir(parents=True, exist_ok=True)

    zip_paths: list[Path] = []
    for url in ARCHIVES:
        p = _load_zip(url, cachedir)
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
                        recs = _parse_massime_xml(xml_data)
                        records.extend(recs)
                        logger.debug(f"  {xml_name}: {len(recs)} record")

    csv_path = outdir / "massime.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(records)
    logger.info(f"\nCSV: {csv_path} ({len(records)} righe)")

    pqt = outdir / "massime.parquet"
    table = pa.Table.from_pylist(records)
    pq.write_table(table, pqt)
    logger.info(f"Parquet: {pqt} ({table.num_rows} righe, {table.num_columns} colonne)")

    _stampa_metriche(records)


if __name__ == "__main__":
    main()
