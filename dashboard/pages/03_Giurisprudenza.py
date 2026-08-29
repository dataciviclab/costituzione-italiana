"""Giurisprudenza — La Corte Costituzionale e i parametri della Costituzione."""

import streamlit as st
import altair as alt
import pandas as pd
from lab_connectors.formatters import fmt_num
from sources import query

st.title("⚖️ Giurisprudenza Costituzionale")
st.markdown(
    "Ogni sentenza della Corte Costituzionale evoca uno o più parametri "
    "della Costituzione. Ecco come vengono usati."
)

# ── KPI ─────────────────────────────────────────────────────────────
df_kpi = query("""
    SELECT
        COUNT(DISTINCT anno_pronuncia || numero_pronuncia) AS n_sentenze,
        COUNT(*) AS n_massime,
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
        SUM(CASE WHEN esito IN ('non_fondata', 'manifestamente_infondata') THEN 1 ELSE 0 END) AS n_respinte
    FROM massime
""")
k = df_kpi.iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("📄 Sentenze", fmt_num(int(k["n_sentenze"])))
k2.metric("📋 Massime", fmt_num(int(k["n_massime"])))
k3.metric("✅ Accolti", fmt_num(int(k["n_accolte"])))
k4.metric("❌ Respinti", fmt_num(int(k["n_respinte"])))

st.markdown("---")

# ── Trend temporale ─────────────────────────────────────────────────
st.subheader("📈 Trend annuale sentenze")

df_trend = query("""
    SELECT
        anno_pronuncia AS anno,
        COUNT(DISTINCT anno_pronuncia || numero_pronuncia) AS n_sentenze,
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte
    FROM massime
    WHERE anno_pronuncia >= 1956
    GROUP BY 1 ORDER BY 1
""")

chart_trend = (
    alt.Chart(df_trend)
    .mark_line(point=True, strokeWidth=2)
    .encode(
        x=alt.X("anno:O", title="Anno", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("n_sentenze:Q", title="N. sentenze"),
        tooltip=[
            "anno",
            alt.Tooltip("n_sentenze:Q", title="Sentenze", format=","),
            alt.Tooltip("n_accolte:Q", title="Accolti", format=","),
        ],
    )
    .properties(height=300)
)
st.altair_chart(chart_trend, use_container_width=True)

st.markdown("---")

# ── Articoli più evocati ────────────────────────────────────────────
st.subheader("🏛️ Articoli più evocati come parametro")

df_param = query("""
    SELECT
        parametro_articolo AS articolo,
        COUNT(*) AS n_volte,
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
        SUM(CASE WHEN esito = 'legittimo' THEN 1 ELSE 0 END) AS n_respinte
    FROM massime
    WHERE parametro_articolo IS NOT NULL AND parametro_articolo != ''
    GROUP BY 1 ORDER BY n_volte DESC
    LIMIT 15
""")
df_param["pct"] = (df_param["n_accolte"] / df_param["n_volte"] * 100).round(1)
df_param["heading"] = "Art. " + df_param["articolo"].astype(str)

chart_param = (
    alt.Chart(df_param)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        y=alt.Y("heading:N", title="", sort="-x"),
        x=alt.X("n_volte:Q", title="N. volte evocato"),
        color=alt.Color(
            "pct:Q",
            title="% accoglimento",
            scale=alt.Scale(scheme="redyellowgreen", domain=[0, 30, 60]),
        ),
        tooltip=[
            "heading",
            alt.Tooltip("n_volte:Q", title="Evocato", format=","),
            alt.Tooltip("n_accolte:Q", title="Accolti", format=","),
            alt.Tooltip("pct:Q", title="% accoglimento", format=".1f"),
        ],
    )
    .properties(height=400)
)
st.altair_chart(chart_param, use_container_width=True)

st.markdown("---")

# ── Distribuzione esiti ─────────────────────────────────────────────
st.subheader("🎯 Distribuzione complessiva esiti")

df_esiti = query("""
    SELECT esito, COUNT(*) AS n
    FROM massime
    GROUP BY esito ORDER BY n DESC
""")

col1, col2 = st.columns(2)
with col1:
    chart_pie = (
        alt.Chart(df_esiti)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta("n:Q"),
            color=alt.Color(
                "esito:N",
                scale=alt.Scale(
                    domain=["illegittimo", "misto", "inammissibile",
                            "non_fondata", "manifestamente_infondata", "altro"],
                    range=["#dc2626", "#f59e0b", "#9ca3af", "#16a34a", "#6b7280", "#a3a3a3"],
                ),
            ),
            tooltip=["esito", alt.Tooltip("n:Q", title="N.", format=",")],
        )
        .properties(height=350)
    )
    st.altair_chart(chart_pie, use_container_width=True)

with col2:
    for _, row in df_esiti.iterrows():
        st.markdown(f"**{row['esito']}** — {fmt_num(int(row['n']))}")

st.caption(
    "Fonte: dati.cortecostituzionale.it · CC BY-SA 3.0 · "
    "Ogni massima = un punto decisorio di una sentenza della Corte Costituzionale"
)
