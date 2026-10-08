"""Test compose iter_costituzionale."""
from __future__ import annotations

from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE = REPO_ROOT / "compose" / "iter-costituzionale"
CLEAN_SQL = COMPOSE / "sql" / "clean.sql"
DATASET_YML = COMPOSE / "dataset.yml"


def _load_yml() -> dict:
    return yaml.safe_load(DATASET_YML.read_text("utf-8"))


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
        entry = support[name]
        assert entry["type"] == "external"
        # Forma dichiarativa registry (no URI GCS hardcoded nel config)
        assert entry["repo"] == "open-politica"
        assert entry["slug"] == name
        assert entry["layer"] == "clean"
        assert entry["years"] == [13, 14, 15, 16, 17, 18, 19]
        assert "uri" not in entry

    tables = [t["name"] for t in cfg["mart"]["tables"]]
    assert "mart_ddl_per_stato" in tables
    assert "mart_funnel_conversione" in tables
    assert "mart_revisioni_con_iter" in tables

    cols = cfg["clean"]["required_columns"]
    assert "join_tier" in cols
    assert "join_method" in cols


def test_sql_usa_placeholder_support():
    """policy: i SQL devono leggere i support via placeholder, non path hardcoded."""
    clean = CLEAN_SQL.read_text("utf-8")
    assert "{support.senato_ddl.outputs}" in clean
    assert "{support.camera_ddl.outputs}" in clean
    assert "{support.camera_leggi.outputs}" in clean
    assert "storage.googleapis.com" not in clean
    assert "../../open-politica" not in clean


def test_support_external_resolves_from_registry():
    """contract: repo+slug+layer risolvono allo stesso template URI GCS di prima."""
    from lab_connectors.gcs.paths import https_url
    from lab_connectors.registry.client import load_registry_local

    workspace_root = REPO_ROOT.parents[1]
    reg_path = workspace_root / "diritto-legge" / "open-politica" / "registry" / "registry.json"
    if not reg_path.is_file():
        return
    reg = load_registry_local(reg_path)
    for slug in ("senato_ddl", "camera_ddl", "camera_leggi"):
        prefix = reg.prefix_for_slug(slug)
        uri = https_url("clean", "clean_parquet", slug=slug, prefix=prefix, year="{year}")
        expected = (
            "https://storage.googleapis.com/dataciviclab-clean/"
            f"open-politica/{slug}/{{year}}/{slug}_{{year}}_clean.parquet"
        )
        assert uri == expected, f"{slug}: {uri} != {expected}"


def test_clean_filtra_costituzionali():
    """policy: filtri camera/senato sui DDL costituzionali, non LIKE libero."""
    clean = CLEAN_SQL.read_text("utf-8")
    assert "natura = 'costituzionale'" in clean
    assert "DI LEGGE COSTITUZIONALE" in clean
    assert "DISEGNO DI LEGGE COSTITUZIONALE" in clean


def test_ha_legge_solo_tier_high():
    """policy: ha_legge solo su join_tier=high (chiavi strutturate)."""
    clean = CLEAN_SQL.read_text("utf-8")
    assert (
        "CASE WHEN m.join_tier = 'high' AND m.rev_urn IS NOT NULL THEN 1 ELSE 0 END AS ha_legge"
        in clean
    )


def test_funnel_conta_leggi_distinte():
    """policy: il funnel distingue DDL da leggi distinte (no overcount sibling)."""
    mart = (COMPOSE / "sql" / "mart_funnel_conversione.sql").read_text("utf-8")
    assert "n_leggi_distinte" in mart
    assert "COUNT(DISTINCT CASE WHEN ha_legge = 1 THEN rev_urn END)" in mart


def test_join_ddl_numero_qualificato_per_legislatura():
    """policy: ddl_numero Camera è per-legislatura — il join deve qualificarlo."""
    clean = CLEAN_SQL.read_text("utf-8")
    assert "d.ddl_numero = c.ddl_numero" in clean
    assert "d.legislatura = c.legislatura" in clean
    # blocco JOIN ddl_to_leggi deve richiedere entrambe le chiavi
    block = clean.split("ddl_to_leggi AS (", 1)[1].split("matched_urn_camera", 1)[0]
    assert "d.ddl_numero = c.ddl_numero" in block
    assert "d.legislatura = c.legislatura" in block
    assert "link_camera_leggi" in block


def test_ddl_numero_cross_leg_non_condivide_urn():
    """policy: stesso ddl_numero su legislature diverse non deve matchare."""
    con = duckdb.connect()
    # camera_leggi: leg13 ha ddl 5148; leg19 ha ddl 976 — stesso intero impossibile
    # ma simuliamo collisione: entrambe ddl_numero=100
    rows = con.execute("""
    WITH leggi AS (
      SELECT * FROM (VALUES
        ('LC2013_1', 100, 13, 'urn:nir:stato:legge.costituzionale:2013;1'),
        ('LC2019_1', 100, 19, 'urn:nir:stato:legge.costituzionale:2019;1')
      ) AS t(legge_camera, ddl_numero, legislatura, urn_normattiva)
    ),
    ddl AS (
      SELECT * FROM (VALUES
        ('camera', '111', 100, 13, 'Modifica articolo 3'),
        ('camera', '222', 100, 19, 'Modifica articolo 9')
      ) AS t(camera_o_senato, atto_num, ddl_numero, legislatura, titolo_norm)
    )
    SELECT d.atto_num, c.urn_normattiva
    FROM ddl d
    JOIN leggi c
      ON d.ddl_numero = c.ddl_numero
     AND d.legislatura = c.legislatura
    """).fetchall()
    assert len(rows) == 2
    assert rows[0][1].endswith("2013;1")
    assert rows[1][1].endswith("2019;1")

    # senza qualifica legislatura: 2×2 = 4 match falsi
    bad = con.execute("""
    WITH leggi AS (
      SELECT * FROM (VALUES
        ('LC2013_1', 100, 13),
        ('LC2019_1', 100, 19)
      ) AS t(legge_camera, ddl_numero, legislatura)
    ),
    ddl AS (
      SELECT * FROM (VALUES
        ('111', 100, 13),
        ('222', 100, 19)
      ) AS t(atto_num, ddl_numero, legislatura)
    )
    SELECT COUNT(*) FROM ddl d JOIN leggi c ON d.ddl_numero = c.ddl_numero
    """).fetchone()[0]
    assert bad == 4, "senza legislatura il join collassa (controprova del bug)"


def test_clean_output_urn_camera_non_null_quando_high():
    """policy: se esiste il clean locale, ogni urn_camera high ha rev_urn."""
    clean_path = (
        REPO_ROOT
        / "out"
        / "data"
        / "clean"
        / "iter_costituzionale"
        / "2026"
        / "iter_costituzionale_2026_clean.parquet"
    )
    if not clean_path.exists():
        return
    con = duckdb.connect()
    bad = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{clean_path}')
        WHERE join_method = 'urn_camera'
          AND join_tier = 'high'
          AND (urn_camera IS NULL OR rev_urn IS NULL)
    """).fetchone()[0]
    assert bad == 0, f"urn_camera high senza URN o rev: {bad}"
