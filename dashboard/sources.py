"""Fonti dati per la dashboard Costituzione Italiana."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

import duckdb
import streamlit as st
from lab_connectors.duckdb.queries import _detect_local_root, _resolve_url

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


def _local_root() -> str | None:
    """Rileva out/data/ locale, con fallback al path del repo."""
    detected = _detect_local_root()
    if detected:
        return detected
    local = _REPO / "out" / "data"
    if local.is_dir():
        return str(local)
    return None


def _clean_url(slug: str, year: int = 2026) -> str:
    lr = _local_root()
    return _resolve_url(
        "clean", "clean_parquet", prefix=PREFIX, local_root=lr, slug=slug, year=year,
    )


def _mart_url(slug: str, table: str, year: int = 2026) -> str:
    lr = _local_root()
    return _resolve_url(
        "mart", "mart_parquet", prefix=PREFIX, local_root=lr, slug=slug, year=year, table=table,
    )


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(database=":memory:")
    for view, slug in SLUGS.items():
        url = _clean_url(slug)
        try:
            if view == "sentenze_complete":
                con.execute(
                    f"CREATE VIEW {view} AS "
                    f"SELECT *, COALESCE(esito,'') AS esito FROM read_parquet('{url}')"
                )
            else:
                con.execute(f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{url}')")
        except Exception:
            con.execute(f"CREATE VIEW {view} AS SELECT NULL AS _missing LIMIT 0")
    return con


@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str) -> pd.DataFrame:
    return get_connection().execute(sql).fetchdf()


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart(slug_key: str, table: str) -> pd.DataFrame:
    slug = SLUGS.get(slug_key, slug_key)
    url = _mart_url(slug, table)
    return duckdb.connect().execute(f"SELECT * FROM read_parquet('{url}')").fetchdf()
