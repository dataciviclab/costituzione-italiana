"""Giudici — L'anagrafica dei giudici costituzionali e la loro provenienza."""

import streamlit as st
import altair as alt
from lab_connectors.formatters import fmt_num
from sources import query

st.title("🏛️ Giudici della Corte Costituzionale")
st.markdown(
    "I giudici costituzionali sono eletti da Parlamento in seduta comune, "
    "Corte di Cassazione, Consiglio di Stato e Corte dei Conti. "
    "Ecco come si distribuiscono per origine e nel tempo."
)

# ── KPI ─────────────────────────────────────────────────────────────
df_kpi = query("""
    SELECT
        COUNT(*) AS n_giudici,
        COUNT(DISTINCT eletto_da) AS n_origini,
        SUM(CASE WHEN data_cessazione IS NOT NULL THEN 1 ELSE 0 END) AS n_cessati,
        SUM(CASE WHEN data_cessazione IS NULL THEN 1 ELSE 0 END) AS n_in_carica
    FROM giudici
""")
k = df_kpi.iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("👤 Giudici", fmt_num(int(k["n_giudici"])))
k2.metric("🏛️ Origini", fmt_num(int(k["n_origini"])))
k3.metric("✅ In carica", fmt_num(int(k["n_in_carica"])))
k4.metric("🔚 Cessati", fmt_num(int(k["n_cessati"])))

st.markdown("---")

# ── Distribuzione per origine ───────────────────────────────────────
st.subheader("🗳️ Giudici per ente elettore")

df_orig = query("""
    SELECT
        eletto_da,
        COUNT(*) AS n_giudici,
        MIN(data_nomina) AS prima_nomina,
        MAX(data_nomina) AS ultima_nomina
    FROM giudici
    WHERE eletto_da IS NOT NULL AND eletto_da != ''
    GROUP BY eletto_da
    ORDER BY n_giudici DESC
""")

col1, col2 = st.columns(2)
with col1:
    chart_orig = (
        alt.Chart(df_orig)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            y=alt.Y("eletto_da:N", title="", sort="-x"),
            x=alt.X("n_giudici:Q", title="N. giudici"),
            color=alt.Color(
                "eletto_da:N",
                legend=None,
                scale=alt.Scale(
                    domain=df_orig["eletto_da"].tolist(),
                    range=["#2563eb", "#059669", "#d97706", "#dc2626", "#8b5cf6"],
                ),
            ),
            tooltip=[
                "eletto_da",
                alt.Tooltip("n_giudici:Q", title="Giudici", format=","),
                "prima_nomina",
                "ultima_nomina",
            ],
        )
        .properties(height=250)
    )
    st.altair_chart(chart_orig, width='stretch')

with col2:
    for _, row in df_orig.iterrows():
        st.markdown(f"**{row['eletto_da']}** — {fmt_num(int(row['n_giudici']))} giudici")

st.markdown("---")

# ── Nomine per decennio ─────────────────────────────────────────────
st.subheader("📅 Nomine per decennio")

df_decennio = query("""
    SELECT
        (year(data_nomina) // 10) * 10 AS decennio,
        eletto_da,
        COUNT(*) AS n_nomine
    FROM giudici
    WHERE data_nomina IS NOT NULL
    GROUP BY 1, 2
    ORDER BY 1, 3 DESC
""")

if not df_decennio.empty:
    chart_dec = (
        alt.Chart(df_decennio)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("decennio:O", title="Decennio"),
            y=alt.Y("n_nomine:Q", title="N. nomine"),
            color=alt.Color("eletto_da:N", title="Eletto da"),
            tooltip=["decennio", "eletto_da", alt.Tooltip("n_nomine:Q", title="Nomine", format=",")],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_dec, width='stretch')

st.markdown("---")

# ── Elenco completo ─────────────────────────────────────────────────
st.subheader("📋 Elenco giudici")

df_elenco = query("""
    SELECT
        nome_cognome,
        titolo,
        eletto_da,
        data_nomina,
        data_giuramento,
        data_cessazione,
        CASE WHEN data_cessazione IS NULL THEN '✅ In carica' ELSE '🔚 Cessato' AS stato
    FROM giudici
    ORDER BY data_nomina DESC
""")

st.dataframe(df_elenco, width='stretch', hide_index=True)

st.caption(
    "Fonte: dati.cortecostituzionale.it · CC BY-SA 3.0 · "
    "Anagrafica dei giudici della Corte Costituzionale dalla sua istituzione"
)
