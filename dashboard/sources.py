"""Fonti dati per la dashboard Costituzione Italiana.

Pattern standard Lab (standards/dashboard.md): wrappa
``lab_connectors.duckdb.queries`` con cache Streamlit. Path resolution
via registry del repo + ``detect_local_root`` (API pubbliche).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

import duckdb
import streamlit as st
from lab_connectors.duckdb import queries as lc_queries
from lab_connectors.gcs.paths import https_url, resolve
from lab_connectors.registry import load_registry_local

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFIX = "costituzione-italiana/"
_registry = load_registry_local(str(REPO_ROOT / "registry" / "registry.json"))

SLUGS = {
    "articoli": "articoli_costituzione",
    "revisioni": "revisioni_costituzionali",
    "atti_promovimento": "atti_promovimento_corte_costituzionale",
    "massime": "massime_corte_costituzionale",
    "citazioni_legislative": "citazioni_costituzionali",
    "pronunce": "pronunce_corte_costituzionale",
    "giudici": "giudici_corte_costituzionale",
    "sentenze_complete": "sentenze_complete",
    "iter_costituzionale": "iter_costituzionale",
}

YEARS = [2026]


def _local_root() -> str | None:
    """out/data/ del repo se presente, altrimenti GCS."""
    return lc_queries.detect_local_root(repo_root=REPO_ROOT)


def _clean_url(slug: str, year: int = 2026) -> str:
    lr = _local_root()
    if lr:
        rel = resolve("clean_parquet", slug=slug, year=str(year))
        return f"{lr}/clean/{rel}"
    return https_url("clean", "clean_parquet", prefix=PREFIX, slug=slug, year=year)


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    """Viste DuckDB su tutti i clean del repo (query multi-dataset)."""
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
def load_mart(slug_key: str, table: str, year: int = 2026) -> pd.DataFrame:
    """Mart table via lab-connectors (registry prefix + auto locale/GCS)."""
    slug = SLUGS.get(slug_key, slug_key)
    return lc_queries.load_mart_table(
        slug,
        table,
        year,
        prefix=PREFIX,
        local_root=_local_root(),
        registry=_registry,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_clean(slug_key: str, year: int = 2026) -> pd.DataFrame:
    slug = SLUGS.get(slug_key, slug_key)
    return lc_queries.load_clean(
        slug,
        [year],
        prefix=PREFIX,
        local_root=_local_root(),
        registry=_registry,
    )


def get_registry():
    """Registry del repo (SQL page e tool lab-connectors)."""
    return _registry
