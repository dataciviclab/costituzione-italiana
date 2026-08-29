"""Citazioni — La Costituzione nella legislazione ordinaria."""

import streamlit as st
import altair as alt
from lab_connectors.formatters import fmt_num
from sources import query

st.title("📝 Citazioni Legislative")
st.markdown(
    "Ogni volta che una legge ordinaria cita un articolo della Costituzione, "
    "lo registriamo. Ecco quali articoli sono più richiamati dal legislatore."
)

# ── KPI ─────────────────────────────────────────────────────────────
df_kpi = query("""
    SELECT
        COUNT(*) AS n_citazioni,
        COUNT(DISTINCT articolo) AS n_articoli,
        COUNT(DISTINCT fonte_filename) AS n_fonti,
        MIN(fonte_anno) AS anno_min,
        MAX(fonte_anno) AS anno_max
    FROM citazioni_legislative
""")
k = df_kpi.iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("📝 Citazioni totali", fmt_num(int(k["n_citazioni"])))
k2.metric("📜 Articoli citati", fmt_num(int(k["n_articoli"])))
k3.metric("📄 Fonti", fmt_num(int(k["n_fonti"])))
k4.metric("📅 Periodo", f"{int(k['anno_min'])}–{int(k['anno_max'])}")

st.markdown("---")

# ── Top articoli citati ─────────────────────────────────────────────
st.subheader("🏆 Articoli più citati")

df_top = query("""
    SELECT articolo, COUNT(*) AS n_citazioni
    FROM citazioni_legislative
    GROUP BY articolo ORDER BY n_citazioni DESC
    LIMIT 20
""")
df_top["heading"] = "Art. " + df_top["articolo"].astype(str)

chart_top = (
    alt.Chart(df_top)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#6366f1")
    .encode(
        y=alt.Y("heading:N", title="", sort="-x"),
        x=alt.X("n_citazioni:Q", title="N. citazioni"),
        tooltip=["heading", alt.Tooltip("n_citazioni:Q", title="Citazioni", format=",")],
    )
    .properties(height=450)
)
st.altair_chart(chart_top, use_container_width=True)

st.markdown("---")

# ── Trend temporale ─────────────────────────────────────────────────
st.subheader("📈 Citazioni nel tempo")

df_trend = query("""
    SELECT fonte_anno AS anno, COUNT(*) AS n_citazioni
    FROM citazioni_legislative
    WHERE fonte_anno >= 1948
    GROUP BY 1 ORDER BY 1
""")

chart_trend = (
    alt.Chart(df_trend)
    .mark_line(point=True, strokeWidth=2, color="#6366f1")
    .encode(
        x=alt.X("anno:O", title="Anno", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("n_citazioni:Q", title="N. citazioni"),
        tooltip=["anno", alt.Tooltip("n_citazioni:Q", title="Citazioni", format=",")],
    )
    .properties(height=280)
)
st.altair_chart(chart_trend, use_container_width=True)

st.markdown("---")

# ── Per tipo di fonte ───────────────────────────────────────────────
st.subheader("📂 Citazioni per tipo di fonte")

df_tipo = query("""
    SELECT fonte_tipo, COUNT(*) AS n
    FROM citazioni_legislative
    GROUP BY 1 ORDER BY n DESC
""")

if not df_tipo.empty:
    chart_tipo = (
        alt.Chart(df_tipo)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#059669")
        .encode(
            y=alt.Y("fonte_tipo:N", title="", sort="-x"),
            x=alt.X("n:Q", title="N. citazioni"),
            tooltip=["fonte_tipo", alt.Tooltip("n:Q", title="Citazioni", format=",")],
        )
        .properties(height=200)
    )
    st.altair_chart(chart_tipo, use_container_width=True)

st.caption(
    "Fonte: italia-corpus · Riferimenti nella legislazione ordinaria "
    "agli articoli della Costituzione Italiana"
)
