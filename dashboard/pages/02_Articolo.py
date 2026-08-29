"""Articolo — Drill-down su un singolo articolo della Costituzione."""

import streamlit as st
import altair as alt
from lab_connectors.formatters import fmt_num
from sources import query

st.title("📜 Esplora un Articolo")

# ── Selectbox ───────────────────────────────────────────────────────
df_all = query("SELECT articolo, heading, parte FROM articoli ORDER BY articolo")
options = {row["heading"]: row["articolo"] for _, row in df_all.iterrows()}

selected = st.selectbox("Scegli un articolo", list(options.keys()))
articolo_n = options[selected]

# ── Dati articolo ───────────────────────────────────────────────────
df_art = query(f"SELECT * FROM articoli WHERE articolo = {articolo_n}")
df_rip = query(f"SELECT * FROM articoli_riepilogo WHERE articolo = {articolo_n}")
df_atti = query(f"""
    SELECT * FROM atti_promovimento
    WHERE parametro_articolo = {articolo_n}
    ORDER BY anno DESC, numero_atto DESC
    LIMIT 50
""")
df_massime = query(f"""
    SELECT esito, COUNT(*) AS n
    FROM massime
    WHERE parametro_articolo = '{articolo_n}'
    GROUP BY esito ORDER BY n DESC
""")
df_cit = query(f"""
    SELECT fonte_collezione, fonte_anno, fonte_tipo, contesto
    FROM citazioni_legislative
    WHERE articolo = {articolo_n}
    ORDER BY fonte_anno DESC
    LIMIT 20
""")

# ── Header ──────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(selected)
    if not df_art.empty:
        testo = df_art["testo"].iloc[0]
        st.markdown(f"> {testo}")

with col2:
    if not df_rip.empty:
        row = df_rip.iloc[0]
        st.metric("🔧 Revisioni", fmt_num(int(row["n_modifiche"])))
        st.metric("⚖️ Giudizi", fmt_num(int(row["n_giudizi"])))
        st.metric("📝 Citazioni", fmt_num(int(row["n_citazioni"])))

st.markdown("---")

# ── Esiti Corte Costituzionale ──────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("⚖️ Esiti della Corte")
    if not df_massime.empty:
        chart = (
            alt.Chart(df_massime)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                y=alt.Y("esito:N", title="", sort="-x"),
                x=alt.X("n:Q", title="N. massime"),
                color=alt.Color(
                    "esito:N",
                    legend=None,
                    scale=alt.Scale(
                        domain=["illegittimo", "misto", "inammissibile",
                                "non_fondata", "manifestamente_infondata", "altro"],
                        range=["#dc2626", "#f59e0b", "#9ca3af", "#16a34a", "#6b7280", "#a3a3a3"],
                    ),
                ),
                tooltip=["esito", alt.Tooltip("n:Q", title="N.", format=",")],
            )
            .properties(height=250)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Nessuna massima trovata per questo articolo.")

with col_b:
    st.subheader("📋 Atti di promovimento")
    if not df_atti.empty:
        st.dataframe(
            df_atti[["anno", "numero_atto", "tipo", "parametro_comma", "n_norme"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nessun atto di promovimento trovato.")

st.markdown("---")

# ── Citazioni legislative ───────────────────────────────────────────
st.subheader("📝 Citazioni nella legislazione")
if not df_cit.empty:
    st.dataframe(
        df_cit,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Nessuna citazione trovata per questo articolo.")
