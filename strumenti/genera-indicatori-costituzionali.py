#!/usr/bin/env python3
"""Genera la mappa articoli della Costituzione ↔ dataset del DataCivicLab.

Legge il clean_catalog da dataset-incubator e incrocia con la mappa
manuale articolo→dataset_slug. Produce data/indicatori-costituzionali.csv/.parquet.

Uso:
    python3 strumenti/genera-indicatori-costituzionali.py [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path

logger = logging.getLogger("genera-indicatori")

CLEAN_CATALOG = (
    Path(__file__).resolve().parent.parent.parent
    / "dataset-incubator"
    / "registry"
    / "clean_catalog.json"
)

# Mappa manuale: articolo → [(dataset_slug, dimensione, tipo_indicatore)]
# dimensione: cosa misura (es. "spesa sanitaria", "disuguaglianza")
# tipo: outcome/strutturale/territoriale
MAPPING: dict[int, list[tuple[str, str, str]]] = {
    # PRINCIPI FONDAMENTALI
    3: [
        ("istat_gini_regionale", "disuguaglianza reddito", "outcome"),
        ("irpef_comunale", "gap reddito territoriale", "territoriale"),
    ],
    5: [
        ("opencivitas_fsc_2025_rso", "Fondo Solidarietà Comunale", "strutturale"),
        # siope_uscite_comuni — da aggiungere quando sarà in clean_catalog
    ],
    9: [
        ("terna_capacita_rinnovabile", "capacità rinnovabile installata", "strutturale"),
        ("terna_electricity_by_source", "mix elettrico per fonte", "outcome"),
        ("ispra_ru_base", "produzione e differenziata rifiuti", "outcome"),
        ("ispra_consumo_suolo", "consumo di suolo", "outcome"),
        ("ispra_emissioni_ghg", "emissioni gas serra", "outcome"),
    ],

    # PARTE I — DIRITTI E DOVERI
    32: [
        ("bdap_lea", "spesa sanitaria regionale", "strutturale"),
        ("aifa_spesa_consumo", "consumo farmaceutico SSN", "outcome"),
        ("strutture_asl", "medici di base e pediatri", "strutturale"),
        ("strutture_ricovero_asl", "posti letto e ricoveri", "strutturale"),
        ("farmacie", "farmacie sul territorio", "strutturale"),
    ],
    33: [
        ("mim_alunni_corso_eta", "alunni per corso ed età", "strutturale"),
        ("mur_contribuzione_universitaria", "contribuzione studentesca", "strutturale"),
    ],
    34: [
        ("mim_alunni_corso_eta", "dispersione scolastica implicita", "outcome"),
    ],
    38: [
        ("inps_pensioni_trimestrale", "numero e importo pensioni", "outcome"),
        ("inps_rdc_pdc", "RdC/PdC per comune", "outcome"),
    ],
    41: [
        ("anac_bandi_gara", "appalti pubblici", "strutturale"),
        ("rna_aiuti_stato", "aiuti di Stato alle imprese", "strutturale"),
    ],
    48: [
        ("elezioni_politiche_2022", "affluenza e risultati elezioni", "outcome"),
    ],
    51: [
        ("dait_amministratori_locali", "anagrafe amministratori locali", "strutturale"),
    ],
    53: [
        ("irpef_comunale", "redditi e imposte per comune", "territoriale"),
        ("mef_irpef_regionale", "redditi per classe e regione", "territoriale"),
        ("istat_gini_regionale", "progressività sistema tributario", "outcome"),
    ],

    # PARTE II — ORDINAMENTO DELLA REPUBBLICA
    81: [
        ("bdap_entrate_stato", "entrate statali", "strutturale"),
        ("bdap_spese_stato", "spese statali", "strutturale"),
    ],
    97: [
        ("dipendenti_pubblici", "occupazione e turnover PA", "strutturale"),
        ("anac_bandi_gara", "trasparenza appalti", "outcome"),
        ("consip_consumi_convenzione", "spesa PA in convenzione", "strutturale"),
    ],
    111: [
        ("civile_flussi", "durata processi civili", "outcome"),
        ("giustizia_penale_indicatori", "clearance rate penale", "outcome"),
    ],
    117: [
        ("opencoesione_progetti", "fondi coesione per regione", "territoriale"),
        ("bdap_entrate_stato", "entrate statali vs regionali", "territoriale"),
    ],
    118: [
        ("opencivitas_fsc_2025_rso", "FSC per comune", "territoriale"),
        ("opencoesione_progetti", "progetti coesione territoriale", "territoriale"),
    ],
    119: [
        ("opencivitas_fsc_2025_rso", "Fondo Solidarietà Comunale", "strutturale"),
        ("irpef_comunale", "autonomia finanziaria comuni", "territoriale"),
    ],
}


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


def genera_mappa(catalog: dict[str, dict]) -> list[dict]:
    """Genera la mappa articolo → dataset."""
    records: list[dict] = []

    for articolo, entries in sorted(MAPPING.items()):
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

    catalog = leggi_clean_catalog(CLEAN_CATALOG)

    # Valida che tutti gli slug MAPPING siano nel catalog
    mapped_slugs = {ds[0] for entries in MAPPING.values() for ds in entries}
    missing_slugs = mapped_slugs - set(catalog.keys())
    if missing_slugs:
        logger.error("Slug non trovati in clean_catalog: %s", sorted(missing_slugs))
        sys.exit(1)

    records = genera_mappa(catalog)

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
