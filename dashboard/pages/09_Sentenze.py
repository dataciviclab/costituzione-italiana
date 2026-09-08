"""Sentenze Complete — Pronunce × massime × giudici: la visione unitaria della Corte."""

import streamlit as st
import altair as alt
from lab_connectors.formatters import fmt_num
from sources import query, load_mart

st.title("⚖️ Sentenze Complete")
st.markdown(
    "La visione unitaria: ogni pronuncia della Corte con il suo esito, "
    "il parametro costituzionale evocato e l'origine del relatore."
)

# ── Carica mart pre-calcolati ───────────────────────────────────────
try:
    df_rel = load_mart("sentenze_complete", "mart_relatore_esiti")
    df_art = load_mart("sentenze_complete", "mart_sentenze_per_articolo")
    has_mart = True
except Exception:
    has_mart = False

if not has_mart:
    st.warning("Mart non disponibili. Esegui `make run-sentenze-complete` per generarli.")
    st.stop()

# ── KPI ─────────────────────────────────────────────────────────────
df_kpi = query("""
    SELECT
        COUNT(*) AS n_righe,
        COUNT(DISTINCT anno_pronuncia || '-' || numero_pronuncia) AS n_sentenze,
        COUNT(DISTINCT relatore_pronuncia) AS n_relatori,
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_illegittime
    FROM sentenze_complete
""")
k = df_kpi.iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("📋 Righe", fmt_num(int(k["n_righe"])))
k2.metric("📄 Sentenze", fmt_num(int(k["n_sentenze"])))
k3.metric("👤 Relatori", fmt_num(int(k["n_relatori"])))
k4.metric("❌ Illegittime", fmt_num(int(k["n_illegittime"])))

st.markdown("---")

# ── Top relatori per illegittime ────────────────────────────────────
st.subheader("👤 Relatori con più sentenze illegittime")

df_top_rel = df_rel.head(15).copy()
df_top_rel["pct_str"] = df_top_rel["pct_illegittime"].astype(str) + "%"

chart_rel = (
    alt.Chart(df_top_rel)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        y=alt.Y("relatore_pronuncia:N", title="", sort="-x"),
        x=alt.X("n_illegittime:Q", title="N. illegittime"),
        color=alt.Color(
            "pct_illegittime:Q",
            title="% illegittime",
            scale=alt.Scale(scheme="redyellowgreen", domain=[0, 15, 30]),
        ),
        tooltip=[
            "relatore_pronuncia",
            alt.Tooltip("n_pronunce:Q", title="Pronunce totali", format=","),
            alt.Tooltip("n_illegittime:Q", title="Illegittime", format=","),
            alt.Tooltip("pct_illegittime:Q", title="% illegittime", format=".1f"),
            alt.Tooltip("n_articoli_diversi:Q", title="Articoli diversi", format=","),
        ],
    )
    .properties(height=450)
)
st.altair_chart(chart_rel, width='stretch')

st.markdown("---")

# ── Articoli per tasso di accoglimento ──────────────────────────────
st.subheader("🏛️ Articoli per tasso di accoglimento")

df_top_art = df_art.head(15).copy()
df_top_art["heading"] = "Art. " + df_top_art["parametro_articolo"].astype(str)

chart_art = (
    alt.Chart(df_top_art)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        y=alt.Y("heading:N", title="", sort="-x"),
        x=alt.X("n_accolte:Q", title="N. accolte"),
        color=alt.Color(
            "pct_accoglimento:Q",
            title="% accoglimento",
            scale=alt.Scale(scheme="redyellowgreen", domain=[0, 10, 20]),
        ),
        tooltip=[
            "heading",
            alt.Tooltip("n_casi:Q", title="Casi totali", format=","),
            alt.Tooltip("n_accolte:Q", title="Accolte", format=","),
            alt.Tooltip("pct_accoglimento:Q", title="% accoglimento", format=".1f"),
            alt.Tooltip("n_relatori:Q", title="Relatori", format=","),
        ],
    )
    .properties(height=450)
)
st.altair_chart(chart_art, width='stretch')

st.markdown("---")

# ── Eletto_da dei relatori ──────────────────────────────────────────
st.subheader("🗳️ Origine dei relatori più attivi")

df_elett = query("""
    SELECT
        relatore_pronuncia,
        relatore_eletto_da,
        COUNT(*) AS n_pronunce,
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_illegittime
    FROM sentenze_complete
    WHERE relatore_pronuncia != '' AND relatore_eletto_da IS NOT NULL
    GROUP BY relatore_pronuncia, relatore_eletto_da
    HAVING n_pronunce >= 10
    ORDER BY n_pronunce DESC
    LIMIT 20
""")

if not df_elett.empty:
    chart_elett = (
        alt.Chart(df_elett)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            y=alt.Y("relatore_pronuncia:N", title="", sort="-x"),
            x=alt.X("n_pronunce:Q", title="N. pronunce"),
            color=alt.Color("relatore_eletto_da:N", title="Eletto da"),
            tooltip=[
                "relatore_pronuncia",
                "relatore_eletto_da",
                alt.Tooltip("n_pronunce:Q", title="Pronunce", format=","),
                alt.Tooltip("n_illegittime:Q", title="Illegittime", format=","),
            ],
        )
        .properties(height=450)
    )
    st.altair_chart(chart_elett, width='stretch')

st.caption(
    "Fonte: dati.cortecostituzionale.it · CC BY-SA 3.0 · "
    "Compose: pronunce × massime × giudici (sentenze_complete)"
)
