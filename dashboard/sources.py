"""Fonti dati per la dashboard Costituzione Italiana.

Strategia: DuckDB legge i parquet direttamente via read_parquet(),
nessun passaggio intermedio DataFrame. Le view vengono créate una volta
e cachate da Streamlit (@st.cache_resource).

- Mart (pre-aggregati, ~8k righe) → caricati subito
- Clean → lazy, creati come view DuckDB su parquet files
"""

from __future__ import annotations

import glob
import logging
from pathlib import Path

import duckdb
import streamlit as st

from lab_connectors.formatters import fmt_num

logger = logging.getLogger(__name__)

# ── Path locale al repo ────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent
_OUT_DATA = _REPO_ROOT / "out" / "data"

# ── Slug dei dataset (dal toolkit pipeline) ──────────────────────
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
    """Trova il path del clean parquet per uno slug."""
    pattern = str(_OUT_DATA / "clean" / slug / str(year) / f"*_{year}_clean.parquet")
    files = glob.glob(pattern)
    return files[0] if files else None


def _mart_path(slug: str, table: str, year: int = 2026) -> str | None:
    """Trova il path del mart parquet per uno slug/table."""
    pattern = str(_OUT_DATA / "mart" / slug / str(year) / f"{table}.parquet")
    files = glob.glob(pattern)
    return files[0] if files else None


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    """DuckDB connection con view sui parquet files direttamente."""
    con = duckdb.connect(database=":memory:")

    for view_name, slug in SLUGS.items():
        path = _clean_path(slug)
        if path:
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
    """Carica un mart come DataFrame pandas."""
    slug = SLUGS.get(slug_key, slug_key)
    path = _mart_path(slug, table)
    if not path:
        raise FileNotFoundError(f"Mart not found: {slug}/{table}")
    con = duckdb.connect(database=":memory:")
    return con.execute(f"SELECT * FROM read_parquet('{path}')").fetchdf()
