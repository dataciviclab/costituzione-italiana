"""Query SQL — Interroga direttamente i dati."""

from pathlib import Path

from lab_connectors.duckdb.sql_page import render_sql_query
from lab_connectors.registry import load_registry_local

_REPO = Path(__file__).resolve().parent.parent.parent

render_sql_query(
    registry=load_registry_local(str(_REPO / "registry" / "registry.json")),
    prefix="costituzione-italiana/",
    default_slug="massime_corte_costituzionale",
    title="🧪 Query SQL",
    description=(
        "Interroga direttamente i dati della Costituzione. "
        "Scrivi SQL su ``clean_input`` — "
        "viene risolta automaticamente sui Parquet GCS."
    ),
)
