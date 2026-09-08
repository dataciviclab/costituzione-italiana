"""Pronunce — Le pronunce della Corte Costituzionale con presidente, relatore, collegio."""

import streamlit as st
import altair as alt
from lab_connectors.formatters import fmt_num
from sources import load_mart

st.title("📋 Pronunce della Corte Costituzionale")
st.markdown(
    "Ogni pronuncia della Corte ha un presidente, un relatore e un collegio. "
    "Ecco chi ha relazionato di più e come si distribuiscono nel tempo."
)

# ── Carica mart ─────────────────────────────────────────────────────
df_rel = load_mart("pronunce", "mart_relatore_per_annuale")
df_pres = load_mart("pronunce", "mart_collegio_composizione")

# ── KPI ─────────────────────────────────────────────────────────────
n_pronunce = int(df_rel["n_pronunce"].sum())
n_relatori = int(df_rel["relatore_pronuncia"].nunique())
n_presidenti = int(df_pres["presidente"].nunique())

k1, k2, k3 = st.columns(3)
k1.metric("📋 Pronunce", fmt_num(n_pronunce))
k2.metric("👤 Relatori", fmt_num(n_relatori))
k3.metric("🏛️ Presidenti", fmt_num(n_presidenti))

st.markdown("---")

# ── Trend per relatore (top 15) ────────────────────────────────────
st.subheader("👤 Relatori più attivi (per anno)")

df_top_rel = (
    df_rel.groupby("relatore_pronuncia", as_index=False)
    .agg(n_pronunce=("n_pronunce", "sum"), n_sentenze=("n_sentenze", "sum"))
    .nlargest(15, "n_pronunce")
)

chart_rel = (
    alt.Chart(df_top_rel)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        y=alt.Y("relatore_pronuncia:N", title="", sort="-x"),
        x=alt.X("n_pronunce:Q", title="N. pronunce"),
        color=alt.Color("n_sentenze:Q", title="Sentenze", scale=alt.Scale(scheme="blues")),
        tooltip=[
            "relatore_pronuncia",
            alt.Tooltip("n_pronunce:Q", title="Pronunce", format=","),
            alt.Tooltip("n_sentenze:Q", title="Sentenze", format=","),
        ],
    )
    .properties(height=400)
)
st.altair_chart(chart_rel, width='stretch')

st.markdown("---")

# ── Top presidenti ──────────────────────────────────────────────────
st.subheader("🏛️ Presidenti più attivi")

df_pres_top = df_pres.nlargest(10, "n_pronunce")

col1, col2 = st.columns(2)
with col1:
    chart_pres = (
        alt.Chart(df_pres_top)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#8b5cf6")
        .encode(
            y=alt.Y("presidente:N", title="", sort="-x"),
            x=alt.X("n_pronunce:Q", title="N. pronunce"),
            tooltip=[
                "presidente",
                alt.Tooltip("n_pronunce:Q", title="Pronunce", format=","),
                "primo_anno",
                "ultimo_anno",
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_pres, width='stretch')

with col2:
    for _, row in df_pres_top.iterrows():
        st.markdown(
            f"**{row['presidente']}** — {fmt_num(int(row['n_pronunce']))} pronunce "
            f"({int(row['primo_anno'])}–{int(row['ultimo_anno'])})"
        )

st.caption(
    "Fonte: dati.cortecostituzionale.it · CC BY-SA 3.0 · "
    "Pronunce = sentenze + ordinanze della Corte Costituzionale"
)
