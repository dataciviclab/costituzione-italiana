"""Test per strumenti/genera-indicatori-costituzionali.py — mapping locale + registry.

Contratto: la mappa articolo→dataset vive nel repo (strumenti/costituzione-mapping.yaml)
e gli slug fanno riferimento alla sezione datasets del registry.json di
dataset-incubator (clean_catalog.json è stato rimosso col fusion ADR).
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MAPPING = REPO_ROOT / "strumenti" / "costituzione-mapping.yaml"


def test_mapping_locale_esiste():
    """Il mapping deve stare nel repo, non più in dataset-incubator."""
    assert MAPPING.exists(), f"{MAPPING} non trovato"


def test_mapping_yaml_valido():
    """Il mapping YAML si parsa e ha la struttura attesa."""
    data = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1
    assert "mapping" in data
    assert len(data["mapping"]) > 0
    for e in data["mapping"]:
        assert e.get("articolo")
        assert e.get("dataset_slug")
        assert e.get("dimensione")
        assert e.get("tipo") in ("outcome", "strutturale", "territoriale")


def test_mapping_slugs_in_di_registry():
    """Gli slug del mapping devono esistere nel registry.json di DI."""
    reg = REPO_ROOT.parent / "dataset-incubator" / "registry" / "registry.json"
    if not reg.exists():
        # Workspace senza dataset-incubator: il contratto reale è coperto dal
        # workflow update-indicatori-da-mapping.
        return
    data = json.loads(reg.read_text(encoding="utf-8"))
    slugs = {d["slug"] for d in data.get("datasets", [])}
    mapping = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
    mapped = {e["dataset_slug"] for e in mapping.get("mapping", [])}
    missing = sorted(mapped - slugs)
    assert not missing, f"slug mancanti dal registry: {missing}"
