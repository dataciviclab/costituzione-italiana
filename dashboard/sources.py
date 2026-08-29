"""Fonti dati per la dashboard Costituzione Italiana.

Legge direttamente i parquet committati in data/ via DuckDB.
Nessuna dipendenza da GCS — tutto locale al repo.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import streamlit as st

from lab_connectors.formatters import fmt_num

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    """DuckDB connection con le viste sui parquet locali."""
    con = duckdb.connect(database=":memory:")

    views = {
        "articoli": "articoli.parquet",
        "revisioni": "revisioni.parquet",
        "atti_promovimento": "atti-promovimento.parquet",
        "massime": "massime.parquet",
        "citazioni_legislative": "citazioni-legislative.parquet",
    }
    for view_name, filename in views.items():
        con.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{DATA_DIR / filename}')"
        )

    # Vista derivata: conteggi per articolo (equivale al master)
    # Definizioni allineate a preprocess.py del compose:
    #   n_giudizi      = atti di promovimento che evocano l'articolo
    #   n_accolte      = massime con esito 'illegittimo'
    #   n_respinte     = massime con esito 'non_fondata' o 'manifestamente_infondata'
    #   n_inammissibili = massime con esito 'inammissibile'
    #   n_modifiche    = revisioni con tipo = 'modifica_costituzione'
    con.execute("""
        CREATE OR REPLACE VIEW articoli_riepilogo AS
        SELECT
            a.articolo,
            a.parte,
            a.titolo,
            a.heading,
            LEFT(a.testo, 200) AS testo_preview,
            COALESCE(r.n_modifiche, 0)   AS n_modifiche,
            COALESCE(g.n_giudizi, 0)     AS n_giudizi,
            COALESCE(m.n_accolte, 0)     AS n_accolte,
            COALESCE(m.n_respinte, 0)    AS n_respinte,
            COALESCE(m.n_inammissibili, 0) AS n_inammissibili,
            COALESCE(c.n_citazioni, 0)   AS n_citazioni
        FROM articoli a
        LEFT JOIN (
            -- Giudizi = atti di promovimento (count from atti-promovimento)
            SELECT TRY_CAST(parametro_articolo AS BIGINT) AS articolo,
                   COUNT(*) AS n_giudizi
            FROM atti_promovimento
            WHERE parametro_articolo IS NOT NULL
            GROUP BY 1
        ) g ON a.articolo = g.articolo
        LEFT JOIN (
            -- Esiti = massime (count by esito)
            SELECT TRY_CAST(parametro_articolo AS BIGINT) AS articolo,
                   SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
                   SUM(CASE WHEN esito IN ('non_fondata', 'manifestamente_infondata') THEN 1 ELSE 0 END) AS n_respinte,
                   SUM(CASE WHEN esito = 'inammissibile' THEN 1 ELSE 0 END) AS n_inammissibili
            FROM massime
            WHERE parametro_articolo IS NOT NULL AND parametro_articolo != ''
            GROUP BY 1
        ) m ON a.articolo = m.articolo
        LEFT JOIN (
            -- Modifiche = solo leggi di revisione costituzionale
            SELECT val AS articolo,
                   COUNT(*) AS n_modifiche
            FROM revisioni, UNNEST(articoli_modificati) AS t(val)
            WHERE val IS NOT NULL
              AND tipo = 'modifica_costituzione'
            GROUP BY 1
        ) r ON a.articolo = r.articolo
        LEFT JOIN (
            SELECT articolo, COUNT(*) AS n_citazioni
            FROM citazioni_legislative
            GROUP BY 1
        ) c ON a.articolo = c.articolo
        ORDER BY a.articolo
    """)

    return con


def query(sql: str) -> "pd.DataFrame":
    """Esegue SQL e restituisce un DataFrame pandas."""
    con = get_connection()
    return con.execute(sql).fetchdf()
