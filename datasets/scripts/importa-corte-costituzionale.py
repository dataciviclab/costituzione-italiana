#!/usr/bin/env python3
"""Scarica e processa i dati della Corte Costituzionale (Atti di promovimento).

Estrae da XML:
- Ogni atto: anno, numero, tipo (ordinanza/ricorso)
- Norma impugnata: descrizione, numero, data, articolo, comma
- Parametro costituzionale evocato: articolo, comma

Produce data/atti-promovimento.csv e .parquet.

Uso:
    python3 strumenti/importa-corte-costituzionale.py [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger("importa-corte")

# URL dei dataset
BASE_URL = "https://dati.cortecostituzionale.it/opendata/Norme_impugnate"
ZIPS = {
    "ordinanza": f"{BASE_URL}/Cc_Opendata_RegistroOrdinanze.zip",
    "ricorso": f"{BASE_URL}/Cc_Opendata_RegistroRicorsi.zip",
}


def _text(elem: ET.Element | None, tag: str) -> str:
    """Testo di un figlio diretto, normalizzato."""
    if elem is None:
        return ""
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def scarica_ed_estrai(temp_dir: str) -> list[dict]:
    """Scarica gli ZIP ed estrae i record."""
    import io
    import zipfile
    import urllib.request

    records: list[dict] = []

    for tipo, url in ZIPS.items():
        logger.info("Download %s da %s…", tipo, url)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            zip_data = resp.read()

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # Trova il file XML dentro lo ZIP
            xml_files = [n for n in zf.namelist() if n.endswith(".xml")]
            if not xml_files:
                logger.warning("Nessun XML trovato in %s", url)
                continue

            xml_path = xml_files[0]
            logger.info("Parsing %s (%s, %d KB)", xml_path, tipo, len(zip_data) // 1024)

            xml_content = zf.read(xml_path)
            records.extend(parse_xml(xml_content, tipo))

    return records


def parse_xml(xml_content: bytes, tipo: str) -> list[dict]:
    """Parsa l'XML e restituisce lista di record."""
    root = ET.fromstring(xml_content)
    records: list[dict] = []

    # Il root può essere <registro_ordinanze> o <registro_ricorsi>
    for atto in root.findall("atto"):
        anno = atto.get("anno", "")
        numero_atto = atto.get("numero", "")

        for np in atto.findall("numero_parte"):
            numero_parte = (np.text or "").strip() or "1"

            # Leggi norme impugnate
            norme_el = np.find("norme")
            norme: list[dict] = []
            if norme_el is not None:
                for norma in norme_el.findall("norma"):
                    norme.append(
                        {
                            "descrizione": _text(norma, "descrizione"),
                            "numero": _text(norma, "numero"),
                            "data": _text(norma, "data"),
                            "articolo": _text(norma, "articolo"),
                            "comma": _text(norma, "comma"),
                            "nesso": _text(norma, "nesso"),
                        }
                    )

            # Leggi parametri costituzionali
            parametri_el = np.find("parametri")
            if parametri_el is None:
                continue

            for param in parametri_el.findall("parametro"):
                descr = _text(param, "descrizione")
                # Solo parametri che sono articoli della Costituzione
                if descr.lower() != "costituzione":
                    continue

                art = _text(param, "articolo")
                if not art:
                    continue

                # Unisci le norme in un'unica stringa
                norme_str = "; ".join(
                    f"{n['descrizione']} n.{n['numero']} art.{n['articolo']} "
                    f"c.{n['comma']}" if n['numero'] else
                    f"{n['descrizione']} art.{n['articolo']} c.{n['comma']}"
                    for n in norme
                )

                records.append(
                    {
                        "tipo": tipo,
                        "anno": int(anno) if anno.isdigit() else 0,
                        "numero_atto": int(numero_atto) if numero_atto.isdigit() else 0,
                        "numero_parte": int(numero_parte) if numero_parte.isdigit() else 1,
                        "parametro_articolo": int(art) if art.isdigit() else 0,
                        "parametro_comma": _text(param, "comma"),
                        "norma_descrizione": norme[0]["descrizione"] if norme else "",
                        "norma_numero": norme[0]["numero"] if norme else "",
                        "norma_articolo": norme[0]["articolo"] if norme else "",
                        "norme_str": norme_str,
                        "n_norme": len(norme),
                    }
                )

    logger.info("Parsati %d record da %s", len(records), tipo)
    return records


def scrivi_csv(records: list[dict], path: Path) -> None:
    campi = [
        "tipo", "anno", "numero_atto", "numero_parte",
        "parametro_articolo", "parametro_comma",
        "norma_descrizione", "norma_numero", "norma_articolo",
        "norme_str", "n_norme",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for rec in records:
            w.writerow({k: rec.get(k, "") for k in campi})
    logger.info("Scritto %s con %d righe", path, len(records))


def scrivi_parquet(records: list[dict], path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table(
        {
            "tipo": [r.get("tipo", "") for r in records],
            "anno": [r.get("anno", 0) for r in records],
            "numero_atto": [r.get("numero_atto", 0) for r in records],
            "numero_parte": [r.get("numero_parte", 1) for r in records],
            "parametro_articolo": [r.get("parametro_articolo", 0) for r in records],
            "parametro_comma": [r.get("parametro_comma", "") for r in records],
            "norma_descrizione": [r.get("norma_descrizione", "") for r in records],
            "norma_numero": [r.get("norma_numero", "") for r in records],
            "norma_articolo": [r.get("norma_articolo", "") for r in records],
            "norme_str": [r.get("norme_str", "") for r in records],
            "n_norme": [r.get("n_norme", 0) for r in records],
        }
    )
    pq.write_table(table, str(path))
    logger.info("Scritto %s", path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("data"))
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="corte-") as tmp:
        records = scarica_ed_estrai(tmp)

    if not records:
        logger.error("Nessun record estratto")
        return

    csv_path = args.output_dir / "atti-promovimento.csv"
    scrivi_csv(records, csv_path)

    parquet_path = args.output_dir / "atti-promovimento.parquet"
    scrivi_parquet(records, parquet_path)

    # Statistiche
    da_tipo = {}
    for r in records:
        da_tipo[r["tipo"]] = da_tipo.get(r["tipo"], 0) + 1

    # Articoli più evocati
    from collections import Counter
    art_count = Counter(r["parametro_articolo"] for r in records)
    top5 = art_count.most_common(5)

    logger.info(
        "Totali: %d parametri costituzionali estratti (%s)",
        len(records),
        ", ".join(f"{k}={v}" for k, v in sorted(da_tipo.items())),
    )
    logger.info("Top 5 articoli evocati: %s", ", ".join(f"art.{a}({n})" for a, n in top5))


if __name__ == "__main__":
    main()
