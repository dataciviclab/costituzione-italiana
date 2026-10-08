"""Policy test compose sentenze-complete — join anagrafica (#30)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE = REPO_ROOT / "compose" / "sentenze-complete"
CLEAN_SQL = COMPOSE / "sql" / "clean.sql"
DATASET_YML = COMPOSE / "dataset.yml"

pytestmark = pytest.mark.policy


def test_clean_esiste():
    assert CLEAN_SQL.is_file()
    assert DATASET_YML.is_file()


def test_clean_matcha_presidente_normalizzato():
    """policy: presidente via cognome/nome normalizzato, non uguaglianza esatta.

    I formati storici sono surname uppercase (SAJA, CAIANIELLO…): l'uguaglianza
    esatta a nome_cognome dava 0 match (#30).
    """
    sql = CLEAN_SQL.read_text(encoding="utf-8")
    assert "presidente_norm" in sql
    assert "cognome_norm" in sql
    assert "presidente_giudice" in sql
    # niente join esatto solo su presidente = nome_cognome
    assert "p.presidente = g.nome_cognome" not in sql


def test_clean_prefisso_solo_se_unico():
    """policy: LIKE prefisso solo se n_cand=1 o match esatto (niente omopoliti)."""
    sql = CLEAN_SQL.read_text(encoding="utf-8")
    assert "n_cand = 1 OR match_rank = 0" in sql
    assert "cognome_norm LIKE" in sql
    # esclude voci collettive multi-persona
    assert "NOT LIKE '% - %'" in sql


def test_clean_relatore_esatto_prima():
    """policy: relatore con uguaglianza esatta prima del fallback normalizzato."""
    sql = CLEAN_SQL.read_text(encoding="utf-8")
    assert "g.nome_cognome = p.relatore_pronuncia" in sql
    assert "relatore_giudice" in sql
    # non deve droppare l'esatto a favore del solo normalizzato
    assert "WHEN g.nome_cognome = p.relatore_pronuncia THEN 0" in sql


def test_required_columns_include_anagrafica():
    import yaml

    cfg = yaml.safe_load(DATASET_YML.read_text(encoding="utf-8"))
    cols = set(cfg["clean"]["required_columns"])
    assert "presidente_giudice" in cols
    assert "relatore_giudice" in cols
    assert "relatore_eletto_da" in cols


def test_sql_usa_placeholder_support():
    sql = CLEAN_SQL.read_text(encoding="utf-8")
    assert "{support.massime.clean}" in sql
    assert "{support.giudici.clean}" in sql
    assert "storage.googleapis.com" not in sql
    assert re.search(r"/home/", sql) is None


def test_residui_dichiarati():
    """I residui noti (#30) non devono introdurre join forzati con alias opachi.

    Omopoliti senza iniziale (GALLO, MARINI, REALE, SANDULLI) e typo
    (CORASANTI vs CORASANITI) restano NULL — non fuzzy arbitrario.
    """
    sql = CLEAN_SQL.read_text(encoding="utf-8")
    # nessun alias hardcodato nel clean
    assert "CORASANTI" not in sql
    assert "CORASANITI" not in sql
