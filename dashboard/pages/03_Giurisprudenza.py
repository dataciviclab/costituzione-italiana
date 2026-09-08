"""Giurisprudenza — La Corte Costituzionale e i parametri della Costituzione."""

import altair as alt
import streamlit as st
from lab_connectors.formatters import fmt_num
from sources import load_mart, query

st.title("⚖️ Giurisprudenza Costituzionale")
st.markdown(
    "Ogni sentenza della Corte Costituzionale evoca uno o più parametri "
    "della Costituzione. Ecco come vengono usati."
)

# ── Carica mart (pre-aggregati, leggeri) ────────────────────────────
df_trend = load_mart("massime", "mart_sentenze_per_annuale")
df_param = load_mart("massime", "mart_parametri_per_annuale")
df_esiti = load_mart("massime", "mart_esiti_per_giudizio")

# ── KPI ─────────────────────────────────────────────────────────────
n_sentenze = int(df_trend["n_sentenze"].sum() or 0)
n_massime = int(df_trend["n_massime"].sum() or 0)
n_accolte = int(df_trend["n_accolte"].sum() or 0)
n_respinte = n_massime - n_accolte  # approssimazione

k1, k2, k3, k4 = st.columns(4)
k1.metric("📄 Sentenze", fmt_num(n_sentenze))
k2.metric("📋 Massime", fmt_num(n_massime))
k3.metric("✅ Accolti", fmt_num(n_accolte))
k4.metric("❌ Respinti", fmt_num(n_respinte))

st.markdown("---")

# ── Trend temporale ─────────────────────────────────────────────────
st.subheader("📈 Trend annuale sentenze")

df_trend_plot = df_trend[["anno_pronuncia", "n_sentenze", "n_accolte"]].copy()
df_trend_plot.columns = ["anno", "n_sentenze", "n_accolte"]
df_trend_plot = df_trend_plot[df_trend_plot["anno"] >= 1956]

chart_trend = (
    alt.Chart(df_trend_plot)
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
st.altair_chart(chart_trend, width='stretch')

st.markdown("---")

# ── Articoli più evocati ────────────────────────────────────────────
st.subheader("🏛️ Articoli più evocati come parametro")

df_param_plot = df_param[df_param["n_volte"] >= 50].nlargest(15, "n_volte").copy()
df_param_plot["heading"] = "Art. " + df_param_plot["parametro_articolo"].astype(str)
df_param_plot["pct"] = (df_param_plot["n_accolte"] / df_param_plot["n_volte"] * 100).round(1)

chart_param = (
    alt.Chart(df_param_plot)
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
st.altair_chart(chart_param, width='stretch')

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
    st.altair_chart(chart_pie, width='stretch')

with col2:
    for _, row in df_esiti.iterrows():
        st.markdown(f"**{row['esito']}** — {fmt_num(int(row['n']))}")

st.caption(
    "Fonte: dati.cortecostituzionale.it · CC BY-SA 3.0 · "
    "Ogni massima = un punto decisorio di una sentenza della Corte Costituzionale"
)
