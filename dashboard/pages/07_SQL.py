"""Query SQL — Interroga direttamente la Costituzione con DuckDB."""

import streamlit as st
from sources import get_connection

st.title("🧪 Query SQL")
st.markdown(
    "Interroga direttamente i dataset della Costituzione con DuckDB. "
    "Le tabelle disponibili sono: ``articoli``, ``revisioni``, "
    "``atti_promovimento``, ``massime``, ``citazioni_legislative``, "
    "``articoli_riepilogo``."
)

# ── Esempi ──────────────────────────────────────────────────────────
examples = {
    "Articoli più evocati in giudizio": """
SELECT parametro_articolo, COUNT(*) AS n
FROM massime
WHERE parametro_articolo IS NOT NULL AND parametro_articolo != ''
GROUP BY 1 ORDER BY n DESC LIMIT 15
""",
    "Tasso di accoglimento per articolo": """
SELECT
    parametro_articolo,
    COUNT(*) AS n_totale,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
    ROUND(SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct
FROM massime
WHERE parametro_articolo IS NOT NULL AND parametro_articolo != ''
GROUP BY 1 HAVING COUNT(*) > 50
ORDER BY pct DESC
""",
    "Articoli mai modificati": """
SELECT a.articolo, a.heading
FROM articoli a
LEFT JOIN (
    SELECT val AS articolo
    FROM revisioni, UNNEST(articoli_modificati) AS t(val)
    WHERE val IS NOT NULL
) r ON a.articolo = r.articolo
WHERE r.articolo IS NULL AND a.articolo IS NOT NULL
ORDER BY a.articolo
""",
    "Citazioni per decennio": """
SELECT (fonte_anno // 10) * 10 AS decennio, COUNT(*) AS n
FROM citazioni_legislative
WHERE fonte_anno >= 1948
GROUP BY 1 ORDER BY 1
""",
}

selected_example = st.selectbox("💡 Esempi", list(examples.keys()))
default_sql = examples[selected_example]

# ── Editor SQL ──────────────────────────────────────────────────────
sql = st.text_area("SQL", value=default_sql.strip(), height=180)

if st.button("▶️ Esegui", type="primary"):
    try:
        con = get_connection()
        result = con.execute(sql).fetchdf()
        st.success(f"{len(result)} righe")
        st.dataframe(result, width='stretch', hide_index=True)
    except Exception as e:
        st.error(f"Errore: {e}")
