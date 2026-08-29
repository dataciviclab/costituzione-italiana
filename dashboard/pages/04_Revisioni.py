"""Revisioni — Le 50 leggi di revisione costituzionale dal 1948."""

import streamlit as st
import altair as alt
import pandas as pd
from lab_connectors.formatters import fmt_num
from sources import query

st.title("🔧 Revisioni Costituzionali")
st.markdown(
    "50 leggi costituzionali dal 1948 a oggi. "
    "Quali articoli sono stati modificati più volte?"
)

# ── Dati ────────────────────────────────────────────────────────────
df_rev = query("""
    SELECT
        urn,
        codice_redazionale,
        data::DATE AS data,
        EXTRACT(YEAR FROM data::DATE) AS anno,
        titolo,
        articoli_modificati,
        n_articoli,
        tipo
    FROM revisioni
    ORDER BY data
""")
df_rev["anno"] = df_rev["anno"].astype(int)

# ── KPI ─────────────────────────────────────────────────────────────
n_rev = len(df_rev)
anno_min = int(df_rev["anno"].min())
anno_max = int(df_rev["anno"].max())
art_mod_unici = len(set(
    int(a) for lista in df_rev["articoli_modificati"]
    if hasattr(lista, "size") and lista.size > 0
    for a in lista
))

k1, k2, k3 = st.columns(3)
k1.metric("🔧 Revisioni totali", fmt_num(n_rev))
k2.metric("📅 Periodo", f"{anno_min}–{anno_max}")
k3.metric("📜 Articoli modificati", fmt_num(art_mod_unici))

st.markdown("---")

# ── Timeline ────────────────────────────────────────────────────────
st.subheader("📅 Distribuzione temporale")

df_timeline = df_rev.groupby("anno").agg(
    n=("codice_redazionale", "count"),
    titoli=("titolo", lambda x: " · ".join(t[:60] + "…" if len(t) > 60 else t for t in x)),
).reset_index()

chart_tl = (
    alt.Chart(df_timeline)
    .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2, color="#2563eb")
    .encode(
        x=alt.X("anno:O", title="Anno", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("n:Q", title="N. revisioni"),
        tooltip=["anno", "n", "titoli"],
    )
    .properties(height=280)
)
st.altair_chart(chart_tl, use_container_width=True)

st.markdown("---")

# ── Articoli più revisionati ────────────────────────────────────────
st.subheader("🏆 Articoli più revisionati")

# Espandi le list e conta
records = []
for _, row in df_rev.iterrows():
    arts = row["articoli_modificati"]
    if hasattr(arts, "size") and arts.size > 0:
        for a in arts:
            records.append({"articolo": int(a), "revisione": row["codice_redazionale"], "anno": row["anno"]})

if records:
    df_exp = pd.DataFrame(records)
    df_counts = (
        df_exp.groupby("articolo")
        .agg(n_modifiche=("revisione", "count"))
        .reset_index()
        .sort_values("n_modifiche", ascending=False)
        .head(15)
    )
    df_counts["heading"] = "Art. " + df_counts["articolo"].astype(str)

    chart_mod = (
        alt.Chart(df_counts)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#d97706")
        .encode(
            y=alt.Y("heading:N", title="", sort="-x"),
            x=alt.X("n_modifiche:Q", title="N. modifiche"),
            tooltip=["heading", alt.Tooltip("n_modifiche:Q", title="Modifiche")],
        )
        .properties(height=380)
    )
    st.altair_chart(chart_mod, use_container_width=True)

st.markdown("---")

# ── Elenco completo ─────────────────────────────────────────────────
st.subheader("📋 Elenco revisioni")

df_display = df_rev[["codice_redazionale", "data", "titolo", "n_articoli"]].copy()
df_display.columns = ["Codice", "Data", "Titolo", "Art. modificati"]
df_display["Data"] = pd.to_datetime(df_display["Data"]).dt.strftime("%d/%m/%Y")

st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)

st.caption(
    "Fonte: italia-corpus · Leggi costituzionali della Repubblica Italiana"
)
