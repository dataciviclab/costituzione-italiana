#!/usr/bin/env python3
"""Genera la mappa articoli della Costituzione ↔ dataset del DataCivicLab.

Legge il clean_catalog da dataset-incubator e la mappa articolo→dataset
da registry/costituzione-mapping.yaml (sempre in dataset-incubator).
Produce data/indicatori-costituzionali.csv/.parquet.

Uso:
    python3 strumenti/genera-indicatori-costituzionali.py [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import logging
from pathlib import Path

import yaml

logger = logging.getLogger("genera-indicatori")

DATASET_INCUBATOR = (
    Path(__file__).resolve().parent.parent.parent / "dataset-incubator"
)
CLEAN_CATALOG = DATASET_INCUBATOR / "registry" / "clean_catalog.json"
MAPPING_YAML = DATASET_INCUBATOR / "registry" / "costituzione-mapping.yaml"

# Mappa letta da registry/costituzione-mapping.yaml in dataset-incubator
# (vedi leggi_mapping_yaml)

def leggi_mapping_yaml(path: Path) -> dict[int, list[tuple[str, str, str]]]:
    """Legge il mapping YAML e restituisce dict articolo → [(slug, dim, tipo), ...]."""
    if not path.exists():
        raise FileNotFoundError(
            f"Mapping YAML non trovato: {path}\n"
            "Assicurati che dataset-incubator sia clonato nel workspace."
        )
    with open(path) as f:
        data = yaml.safe_load(f)
    mapping: dict[int, list[tuple[str, str, str]]] = {}
    for entry in data.get("mapping", []):
        art = entry.get("articolo")
        slug = entry.get("dataset_slug")
        dim = entry.get("dimensione", "")
        tipo = entry.get("tipo", "outcome")
        if art and slug:
            mapping.setdefault(art, []).append((slug, dim, tipo))
    logger.info("Letto mapping YAML: %d articoli", len(mapping))
    return mapping


def leggi_clean_catalog(path: Path) -> dict[str, dict]:
    """Legge il clean_catalog e restituisce dict slug → info."""
    if not path.exists():
        raise FileNotFoundError(
            f"clean_catalog non trovato: {path}\n"
            "Assicurati che dataset-incubator sia clonato nel workspace."
        )
    with open(path) as f:
        catalog = json.load(f)
    slugs: dict[str, dict] = {}
    for ds in catalog.get("datasets", []):
        slug = ds.get("slug", "")
        if slug:
            slugs[slug] = ds
    logger.info("Letto clean_catalog: %d dataset", len(slugs))
    return slugs


def genera_mappa(
    mapping: dict[int, list[tuple[str, str, str]]],
    catalog: dict[str, dict],
) -> list[dict]:
    """Genera la mappa articolo → dataset."""
    records: list[dict] = []

    for articolo, entries in sorted(mapping.items()):
        for ds_slug, dimensione, tipo in entries:
            ds_info = catalog.get(ds_slug, {})
            records.append(
                {
                    "articolo": articolo,
                    "dataset_slug": ds_slug,
                    "dataset_name": ds_info.get("name", ds_slug),
                    "fonte": ds_info.get("source", ""),
                    "dimensione": dimensione,
                    "tipo_indicatore": tipo,
                }
            )

    return records


def scrivi_csv(records: list[dict], path: Path) -> None:
    campi = ["articolo", "dataset_slug", "dataset_name", "fonte", "dimensione", "tipo_indicatore"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        for rec in records:
            w.writerow(rec)
    logger.info("Scritto %s con %d righe", path, len(records))


def scrivi_parquet(records: list[dict], path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table(
        {
            "articolo": [r["articolo"] for r in records],
            "dataset_slug": [r["dataset_slug"] for r in records],
            "dataset_name": [r["dataset_name"] for r in records],
            "fonte": [r["fonte"] for r in records],
            "dimensione": [r["dimensione"] for r in records],
            "tipo_indicatore": [r["tipo_indicatore"] for r in records],
        }
    )
    pq.write_table(table, str(path))
    logger.info("Scritto %s", path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("data"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

    mapping = leggi_mapping_yaml(MAPPING_YAML)
    catalog = leggi_clean_catalog(CLEAN_CATALOG)

    # Valida che tutti gli slug del mapping siano nel catalog
    mapped_slugs = {ds[0] for entries in mapping.values() for ds in entries}
    missing_slugs = mapped_slugs - set(catalog.keys())
    if missing_slugs:
        logger.error(
            "Slug nel mapping YAML ma non in clean_catalog: %s. "
            "Correggi il mapping o pubblica i dataset mancanti.",
            sorted(missing_slugs),
        )
        sys.exit(1)

    records = genera_mappa(mapping, catalog)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scrivi_csv(records, args.output_dir / "indicatori-costituzionali.csv")
    scrivi_parquet(records, args.output_dir / "indicatori-costituzionali.parquet")

    articoli_coperti = sorted(set(r["articolo"] for r in records))
    logger.info(
        "Mappati %d indicatori per %d articoli della Costituzione",
        len(records),
        len(articoli_coperti),
    )


if __name__ == "__main__":
    main()
