"""Panoramica — La Costituzione italiana in numeri."""

import streamlit as st
import altair as alt
import pandas as pd
from lab_connectors.formatters import fmt_num
from sources import query

st.title("📊 La Costituzione in Numeri")
st.markdown(
    "139 articoli, 18 disposizioni transitorie, 78 anni di storia. "
    "Ogni dato collegato alla Costituzione: revisioni, giurisprudenza, citazioni, attuazione."
)

# ── KPI ─────────────────────────────────────────────────────────────
df = query("SELECT * FROM articoli_riepilogo")

n_articoli = len(df)
n_parti = df["parte"].nunique()
n_modifiche = int(df["n_modifiche"].sum())
n_giudizi = int(df["n_giudizi"].sum())
n_accolte = int(df["n_accolte"].sum())
n_respinte = int(df["n_respinte"].sum())
n_citazioni = int(df["n_citazioni"].sum())
n_revisioni = int(query("SELECT COUNT(*) as n FROM revisioni").iloc[0]["n"])

k1, k2, k3, k4 = st.columns(4)
k1.metric("📜 Articoli", fmt_num(n_articoli))
k2.metric("⚖️ Giudizi Corte", fmt_num(n_giudizi))
k3.metric("📝 Citazioni legislative", fmt_num(n_citazioni))
k4.metric("🔧 Leggi di revisione", fmt_num(n_revisioni))

k5, k6, k7 = st.columns(3)
k5.metric("✅ Accolti", fmt_num(n_accolte))
k6.metric("❌ Respinti", fmt_num(n_respinte))
k7.metric("🎯 Tasso accoglimento", f"{n_accolte / (n_accolte + n_respinte + int(df['n_inammissibili'].sum())) * 100:.1f}%" if (n_accolte + n_respinte) else "—")

st.markdown("---")

# ── Heatmap per parte della Costituzione ────────────────────────────
st.subheader("🗺️ Mappa della Costituzione")

parti_order = [
    "Principi fondamentali",
    "Parte prima: diritti e doveri dei cittadini",
    "Parte seconda: ordinamento della repubblica",
]
df["parte_ord"] = pd.Categorical(df["parte"], categories=parti_order, ordered=True)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Articoli per parte**")
    df_parti = (
        df.groupby("parte_ord", observed=True)
        .agg(n_articoli=("articolo", "count"), n_giudizi=("n_giudizi", "sum"))
        .reset_index()
    )
    chart_parti = (
        alt.Chart(df_parti)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("n_articoli:Q", title="N. articoli"),
            y=alt.Y("parte_ord:N", title="", sort=parti_order),
            color=alt.Color("parte_ord:N", legend=None, scale=alt.Scale(
                domain=parti_order,
                range=["#2563eb", "#059669", "#d97706"],
            )),
            tooltip=[
                "parte_ord",
                alt.Tooltip("n_articoli:Q", title="Articoli", format=","),
                alt.Tooltip("n_giudizi:Q", title="Giudizi", format=","),
            ],
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
                domain=parti_order,
                range=["#2563eb", "#059669", "#d97706"],
            )),
            tooltip=[
                "parte_ord",
                alt.Tooltip("n_giudizi:Q", title="Giudizi", format=","),
            ],
        )
        .properties(height=180)
    )
    st.altair_chart(chart_giudizi, width='stretch')

st.markdown("---")

# ── Treemap: articoli più "controversi" ─────────────────────────────
st.subheader("🔥 Articoli più contestati")
st.markdown("I 10 articoli con più giudizi di legittimità davanti alla Corte Costituzionale.")

df_top = (
    df.nlargest(10, "n_giudizi")[
        ["heading", "parte", "n_giudizi", "n_accolte", "n_respinte", "n_inammissibili"]
    ]
    .reset_index(drop=True)
)
df_top["pct_accoglimento"] = (
    df_top["n_accolte"] / (df_top["n_accolte"] + df_top["n_respinte"] + df_top["n_inammissibili"]) * 100
).round(1)

chart_top = (
    alt.Chart(df_top)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        y=alt.Y("heading:N", title="", sort="-x"),
        x=alt.X("n_giudizi:Q", title="N. giudizi"),
        color=alt.Color(
            "pct_accoglimento:Q",
            title="% accoglimento",
            scale=alt.Scale(scheme="redyellowgreen", domain=[0, 50, 100]),
        ),
        tooltip=[
            "heading",
            alt.Tooltip("n_giudizi:Q", title="Giudizi", format=","),
            alt.Tooltip("n_accolte:Q", title="Accolti", format=","),
            alt.Tooltip("n_respinte:Q", title="Respinti", format=","),
            alt.Tooltip("pct_accoglimento:Q", title="% accoglimento", format=".1f"),
        ],
    )
    .properties(height=350)
)
st.altair_chart(chart_top, width='stretch')

st.markdown("---")

# ── Top citazioni ───────────────────────────────────────────────────
st.subheader("📝 Articoli più citati nella legislazione")

df_cit = df.nlargest(10, "n_citazioni")[["heading", "n_citazioni", "parte"]].reset_index(drop=True)

chart_cit = (
    alt.Chart(df_cit)
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
