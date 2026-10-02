"""Test compose iter_costituzionale."""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE = REPO_ROOT / "compose" / "iter-costituzionale"


def _load_yml() -> dict:
    return yaml.safe_load((COMPOSE / "dataset.yml").read_text("utf-8"))


def test_config_esiste():
    """contract: il config del compose deve esistere."""
    assert (COMPOSE / "dataset.yml").exists()
    assert (COMPOSE / "sql" / "clean.sql").exists()


def test_config_schema_minimo():
    """contract: nome dataset, raw revisioni, support open-politica, mart obbligatori."""
    cfg = _load_yml()
    assert cfg["dataset"]["name"] == "iter_costituzionale"
    assert cfg["dataset"]["years"] == [2026]

    raw_names = [s["name"] for s in cfg["raw"]["sources"]]
    assert "revisioni" in raw_names

    support = {s["name"]: s for s in cfg["support"]}
    assert "senato_ddl" in support
    assert "camera_ddl" in support
    assert "camera_leggi" in support
    for name in ("senato_ddl", "camera_ddl", "camera_leggi"):
        assert support[name]["type"] == "external"
        assert "{year}" in support[name]["uri"]

    tables = [t["name"] for t in cfg["mart"]["tables"]]
    assert "mart_ddl_per_stato" in tables
    assert "mart_funnel_conversione" in tables
    assert "mart_revisioni_con_iter" in tables

    cols = cfg["clean"]["required_columns"]
    assert "join_tier" in cols
    assert "join_method" in cols


def test_sql_usa_placeholder_support():
    """policy: i SQL devono leggere i support via placeholder, non path hardcoded."""
    clean = (COMPOSE / "sql" / "clean.sql").read_text("utf-8")
    assert "{support.senato_ddl.outputs}" in clean
    assert "{support.camera_ddl.outputs}" in clean
    assert "{support.camera_leggi.outputs}" in clean
    assert "storage.googleapis.com" not in clean
    assert "../../open-politica" not in clean


def test_clean_filtra_costituzionali():
    """policy: filtri camera/senato sui DDL costituzionali, non LIKE libero."""
    clean = (COMPOSE / "sql" / "clean.sql").read_text("utf-8")
    assert "natura = 'costituzionale'" in clean
    assert "DI LEGGE COSTITUZIONALE" in clean
    assert "DISEGNO DI LEGGE COSTITUZIONALE" in clean


def test_ha_legge_solo_tier_high():
    """policy: ha_legge solo su join_tier=high (chiavi strutturate)."""
    clean = (COMPOSE / "sql" / "clean.sql").read_text("utf-8")
    assert (
        "CASE WHEN m.join_tier = 'high' AND m.rev_urn IS NOT NULL THEN 1 ELSE 0 END AS ha_legge"
        in clean
    )


def test_funnel_conta_leggi_distinte():
    """policy: il funnel distingue DDL da leggi distinte (no overcount sibling)."""
    mart = (COMPOSE / "sql" / "mart_funnel_conversione.sql").read_text("utf-8")
    assert "n_leggi_distinte" in mart
    assert "COUNT(DISTINCT CASE WHEN ha_legge = 1 THEN rev_urn END)" in mart
