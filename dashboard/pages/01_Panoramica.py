"""Panoramica — La Costituzione italiana in numeri."""

import altair as alt
import pandas as pd
import streamlit as st
from lab_connectors.formatters import fmt_num
from sources import query

st.title("📊 La Costituzione in Numeri")

# ── KPI ─────────────────────────────────────────────────────────────
df_kpi = query("""
    SELECT
        (SELECT COUNT(*) FROM articoli) AS n_articoli,
        (SELECT COUNT(*) FROM revisioni) AS n_modifiche,
        (SELECT COUNT(*) FROM atti_promovimento) AS n_giudizi,
        (SELECT COUNT(*) FROM citazioni_legislative) AS n_citazioni,
        (SELECT COUNT(*) FROM pronunce) AS n_pronunce
""")
k = df_kpi.iloc[0]
n_articoli = int(k["n_articoli"])
n_modifiche = int(k["n_modifiche"])
n_giudizi = int(k["n_giudizi"])
n_citazioni = int(k["n_citazioni"])
n_pronunce = int(k["n_pronunce"])

df_esiti = query("""
    SELECT
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
        SUM(CASE WHEN esito IN ('non_fondata', 'manifestamente_infondata') THEN 1 ELSE 0 END) AS n_respinte,
        SUM(CASE WHEN esito = 'inammissibile' THEN 1 ELSE 0 END) AS n_inammissibili
    FROM massime
""")
n_accolte = int(df_esiti.iloc[0]["n_accolte"])
n_respinte = int(df_esiti.iloc[0]["n_respinte"])
n_inammissibili = int(df_esiti.iloc[0]["n_inammissibili"])

k1, k2, k3, k4 = st.columns(4)
k1.metric("📜 Articoli", fmt_num(n_articoli))
k2.metric("⚖️ Giudizi Corte", fmt_num(n_giudizi))
k3.metric("📝 Citazioni legislative", fmt_num(n_citazioni))
k4.metric("📋 Pronunce", fmt_num(n_pronunce))

k5, k6, k7 = st.columns(3)
k5.metric("✅ Accolti", fmt_num(n_accolte))
k6.metric("❌ Respinti", fmt_num(n_respinte))
total = n_accolte + n_respinte + n_inammissibili
k7.metric("🎯 Tasso accoglimento", f"{n_accolte / total * 100:.1f}%" if total else "—")

st.markdown("---")

# ── Heatmap per parte ───────────────────────────────────────────────
st.subheader("🗺️ Mappa della Costituzione")

parti_order = [
    "Principi fondamentali",
    "Parte prima: diritti e doveri dei cittadini",
    "Parte seconda: ordinamento della repubblica",
]

df_heat = query("""
    SELECT
        a.parte,
        a.articolo,
        a.heading,
        COUNT(*) AS n_giudizi
    FROM atti_promovimento ap
    JOIN articoli a ON TRY_CAST(ap.parametro_articolo AS BIGINT) = a.articolo
    WHERE ap.parametro_articolo IS NOT NULL
    GROUP BY 1, 2, 3
""")
df_heat["parte_ord"] = pd.Categorical(df_heat["parte"], categories=parti_order, ordered=True)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Articoli per parte**")
    df_parti = (
        df_heat.groupby("parte_ord", observed=True)
        .agg(n_articoli=("articolo", "nunique"), n_giudizi=("n_giudizi", "sum"))
        .reset_index()
    )
    chart_parti = (
        alt.Chart(df_parti)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("n_articoli:Q", title="N. articoli"),
            y=alt.Y("parte_ord:N", title="", sort=parti_order),
            color=alt.Color("parte_ord:N", legend=None, scale=alt.Scale(
                domain=parti_order, range=["#2563eb", "#059669", "#d97706"],
            )),
        )
        .properties(height=180)
    )
    st.altair_chart(chart_parti, width='stretch')

with col_right:
    st.markdown("**Giudizi per parte**")
    chart_giudizi = (
        alt.Chart(df_parti)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("n_giudizi:Q", title="N. giudizi"),
            y=alt.Y("parte_ord:N", title="", sort=parti_order),
            color=alt.Color("parte_ord:N", legend=None, scale=alt.Scale(
                domain=parti_order, range=["#2563eb", "#059669", "#d97706"],
            )),
        )
        .properties(height=180)
    )
    st.altair_chart(chart_giudizi, width='stretch')

st.markdown("---")

# ── Articoli più contestati ─────────────────────────────────────────
st.subheader("🔥 Articoli più contestati")

df_top = (
    df_heat.nlargest(10, "n_giudizi")[["heading", "parte", "n_giudizi"]]
    .reset_index(drop=True)
)

chart_top = (
    alt.Chart(df_top)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#dc2626")
    .encode(
        y=alt.Y("heading:N", title="", sort="-x"),
        x=alt.X("n_giudizi:Q", title="N. giudizi"),
        tooltip=["heading", alt.Tooltip("n_giudizi:Q", title="Giudizi", format=",")],
    )
    .properties(height=300)
)
st.altair_chart(chart_top, width='stretch')

st.markdown("---")

# ── Top citazioni ───────────────────────────────────────────────────
st.subheader("📝 Articoli più citati nella legislazione")

df_cit_top = query("""
    SELECT a.heading, COUNT(*) AS n_citazioni
    FROM citazioni_legislative c
    JOIN articoli a ON c.articolo = a.articolo
    GROUP BY 1 ORDER BY 2 DESC LIMIT 10
""")

chart_cit = (
    alt.Chart(df_cit_top)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#6366f1")
    .encode(
        y=alt.Y("heading:N", title="", sort="-x"),
        x=alt.X("n_citazioni:Q", title="N. citazioni"),
        tooltip=["heading", alt.Tooltip("n_citazioni:Q", title="Citazioni", format=",")],
    )
    .properties(height=300)
)
st.altair_chart(chart_cit, width='stretch')

st.caption(
    "Fonte: costituzione-italiana · DataCivicLab · "
    "Testo: Wikisource CC BY-SA 3.0 · Giurisprudenza: Corte Costituzionale CC BY-SA 3.0"
)
