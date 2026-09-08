"""Fonti dati per la dashboard Costituzione Italiana.

In dev: legge da out/data/ (auto-rilevato).
In prod (Streamlit Cloud): legge da GCS via HTTPS (nessun local_root).
"""

from __future__ import annotations

import glob
import logging
from pathlib import Path

import duckdb
import streamlit as st

from lab_connectors.formatters import fmt_num

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────
PREFIX = "costituzione-italiana/"

_REPO_ROOT = Path(__file__).resolve().parent.parent
_OUT_DATA = _REPO_ROOT / "out" / "data"

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


def _clean_path(slug: str, year: int = 2026) -> str | None:
    """Trova il path del clean parquet per uno slug (solo locale)."""
    pattern = str(_OUT_DATA / "clean" / slug / str(year) / f"*_{year}_clean.parquet")
    files = glob.glob(pattern)
    return files[0] if files else None


def _mart_path(slug: str, table: str, year: int = 2026) -> str | None:
    """Trova il path del mart parquet (solo locale)."""
    pattern = str(_OUT_DATA / "mart" / slug / str(year) / f"{table}.parquet")
    files = glob.glob(pattern)
    return files[0] if files else None


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    """DuckDB connection con view sui parquet files."""
    con = duckdb.connect(database=":memory:")

    for view_name, slug in SLUGS.items():
        path = _clean_path(slug)
        if path:
            if view_name == "sentenze_complete":
                con.execute(
                    f"CREATE OR REPLACE VIEW {view_name} AS "
                    f"SELECT *, COALESCE(esito, '') AS esito "
                    f"FROM read_parquet('{path}')"
                )
            else:
                con.execute(
                    f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{path}')"
                )
            logger.info(f"View {view_name} → {Path(path).name}")
        else:
            con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT NULL AS _missing LIMIT 0")
            logger.warning(f"View {view_name}: parquet not found")

    return con


def query(sql: str):
    """Esegue SQL e restituisce un DataFrame pandas."""
    con = get_connection()
    return con.execute(sql).fetchdf()


def load_mart(slug_key: str, table: str):
    """Carica un mart come DataFrame. Locale da out/ o GCS via lab_connectors."""
    from lab_connectors.duckdb.queries import load_mart_table

    slug = SLUGS.get(slug_key, slug_key)
    # Prova locale prima, poi GCS
    path = _mart_path(slug, table)
    if path:
        con = duckdb.connect(database=":memory:")
        return con.execute(f"SELECT * FROM read_parquet('{path}')").fetchdf()
    # Fallback GCS (production)
    return load_mart_table(slug, table, YEARS[0], prefix=PREFIX)
