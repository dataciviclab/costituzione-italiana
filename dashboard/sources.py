"""Fonti dati per la dashboard Costituzione Italiana.

Strategia di caricamento:
- Mart (pre-aggregati, ~8k righe) → caricati subito, leggeri
- Clean (~576k righe) → lazy load, solo quando servono

Le pagine usano query() per SQL arbitrario su viste già caricate,
oppure load_mart() per dati pre-calcolati.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import streamlit as st

from lab_connectors.duckdb.queries import load_clean, load_mart_table
from lab_connectors.formatters import fmt_num

logger = logging.getLogger(__name__)

# ── Path locale al repo ────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_ROOT = str(_REPO_ROOT / "out" / "data")

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


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    """DuckDB connection — lazy, le view vengono popolate da load_clean_view."""
    con = duckdb.connect(database=":memory:")
    for view_name in SLUGS:
        con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT NULL AS _missing LIMIT 0")
    return con


def load_clean_view(view_name: str) -> None:
    """Carica un clean layer specifico (lazy, una volta sola)."""
    con = get_connection()
    # Se la vista ha già dei dati, non ricaricare
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
        if n > 0:
            return
    except Exception:
        pass

    slug = SLUGS.get(view_name)
    if not slug:
        logger.warning(f"Unknown view: {view_name}")
        return

    try:
        df = load_clean(slug, YEARS, local_root=LOCAL_ROOT)
        con.register(f"_raw_{view_name}", df)
        con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM _raw_{view_name}")
        logger.info(f"Loaded {view_name}: {len(df)} rows")
    except Exception as e:
        logger.warning(f"Failed to load {view_name} ({slug}): {e}")
        con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT NULL AS _missing LIMIT 0")


def query(sql: str) -> "pd.DataFrame":
    """Esegue SQL e restituisce un DataFrame pandas."""
    con = get_connection()
    return con.execute(sql).fetchdf()


def load_mart(slug_key: str, table: str) -> "pd.DataFrame":
    """Carica un singolo mart table dal pipeline."""
    slug = SLUGS.get(slug_key, slug_key)
    return load_mart_table(slug, table, YEARS[0], local_root=LOCAL_ROOT)
