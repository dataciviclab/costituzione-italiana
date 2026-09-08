"""Fonti dati per la dashboard Costituzione Italiana."""

from __future__ import annotations

import glob
from pathlib import Path

import duckdb
import streamlit as st

from lab_connectors.duckdb.queries import load_mart_table
from lab_connectors.gcs.paths import https_url
from lab_connectors.formatters import fmt_num

PREFIX = "costituzione-italiana/"
_REPO = Path(__file__).resolve().parent.parent
_LOCAL = _REPO / "out" / "data"

SLUGS = {
    "articoli": "articoli_costituzione",
    "revisioni": "revisioni_costituzionali",
    "atti_promovimento": "atti_promovimento_corte_costituzionale",
    "massime": "massime_corte_costituzionale",
    "citazioni_legislative": "citazioni_costituzionali",
    "pronunce": "pronunce_corte_costituzionale",
    "giudici": "giudici_corte_costituzionale",
    "sentenze_complete": "sentenze_complete",
}

YEARS = [2026]


def _clean_url(slug: str, year: int = 2026) -> str:
    local = glob.glob(str(_LOCAL / "clean" / slug / str(year) / f"*_{year}_clean.parquet"))
    if local:
        return local[0]
    return https_url("clean", "clean_parquet", prefix=PREFIX, slug=slug, year=year)


def _mart_url(slug: str, table: str, year: int = 2026) -> str:
    local = glob.glob(str(_LOCAL / "mart" / slug / str(year) / f"{table}.parquet"))
    if local:
        return local[0]
    return https_url("mart", "mart_parquet", prefix=PREFIX, slug=slug, year=year, table=table)


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(database=":memory:")
    for view, slug in SLUGS.items():
        url = _clean_url(slug)
        try:
            if view == "sentenze_complete":
                con.execute(f"CREATE VIEW {view} AS SELECT *, COALESCE(esito,'') AS esito FROM read_parquet('{url}')")
            else:
                con.execute(f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{url}')")
        except Exception:
            con.execute(f"CREATE VIEW {view} AS SELECT NULL AS _missing LIMIT 0")
    return con


def query(sql: str):
    return get_connection().execute(sql).fetchdf()


def load_mart(slug_key: str, table: str):
    slug = SLUGS.get(slug_key, slug_key)
    url = _mart_url(slug, table)
    return duckdb.connect().execute(f"SELECT * FROM read_parquet('{url}')").fetchdf()
