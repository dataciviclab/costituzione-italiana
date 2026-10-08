"""Iter Costituzionale — DDL Camera/Senato × revisioni promulgate.

Compose: quante proposte di revisione arrivano a legge, dove si fermano.
"""

import altair as alt
import streamlit as st
from lab_connectors.formatters import fmt_num, fmt_pct
from sources import load_mart

st.title("🔁 Iter Costituzionale")
st.markdown(
    "DDL di Camera e Senato a natura costituzionale joinati alle "
    "50 leggi di revisione promulgate. Join tri-tier: high = chiavi "
    "strutturate (URN camera / data+numero), medium = titolo."
)

# ── Funnel conversione ──────────────────────────────────────────────
st.subheader("📉 Funnel: proposte → leggi")

try:
    df_funnel = load_mart("iter_costituzionale", "mart_funnel_conversione")
except Exception as exc:  # noqa: BLE001 — UI dashboard
    st.error(f"Mart non disponibile: {exc}")
    st.stop()

if df_funnel.empty:
    st.warning("Nessun dato nel funnel di conversione.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
tot_proposte = int(df_funnel["n_proposte"].sum())
tot_leggi = int(df_funnel["n_leggi_distinte"].sum())
tot_high = int(df_funnel["n_tier_high"].sum())
pct_conversione = (tot_leggi / tot_proposte) if tot_proposte else 0.0
k1.metric("Proposte", fmt_num(tot_proposte))
k2.metric("Leggi distinte (join high)", fmt_num(tot_leggi))
k3.metric("Join ad alta confidenza", fmt_num(tot_high))
k4.metric("Conversione", fmt_pct(pct_conversione))

# Barre per ramo
chart_funnel = (
    alt.Chart(df_funnel)
    .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
    .encode(
        x=alt.X("legislatura:O", title="Legislatura"),
        y=alt.Y("n_proposte:Q", title="Proposte", stack=None),
        color=alt.Color("camera_o_senato:N", title="Ramo", scale=alt.Scale(range=["#2563eb", "#dc2626"])),
        tooltip=[
            "camera_o_senato",
            "legislatura",
            "n_proposte",
            "n_con_legge",
            "n_leggi_distinte",
            "pct_conversione",
        ],
    )
    .properties(height=300)
)
st.altair_chart(chart_funnel, width="stretch")

st.markdown("---")

# ── Stati iter ──────────────────────────────────────────────────────
st.subheader("📍 Stati dell'iter per ramo e legislatura")

df_stati = load_mart("iter_costituzionale", "mart_ddl_per_stato")
chart_stati = (
    alt.Chart(df_stati)
    .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
    .encode(
        x=alt.X("legislatura:O", title="Legislatura"),
        y=alt.Y("n_proposte:Q", title="DDL"),
        color=alt.Color("stato:N", title="Stato"),
        row=alt.Row("camera_o_senato:N", title="Ramo"),
        tooltip=["camera_o_senato", "legislatura", "stato", "n_proposte", "n_con_legge_high"],
    )
    .properties(height=180)
)
st.altair_chart(chart_stati, width="stretch")

with st.expander("Tabella stati"):
    st.dataframe(
        df_stati.sort_values(["camera_o_senato", "legislatura", "n_proposte"], ascending=[True, True, False]),
        width="stretch",
        hide_index=True,
    )

st.markdown("---")

# ── Revisioni con iter ──────────────────────────────────────────────
st.subheader("✅ Revisioni promulgate e collegamenti DDL")

df_rev = load_mart("iter_costituzionale", "mart_revisioni_con_iter")

k1, k2, k3 = st.columns(3)
k1.metric("Revisioni in mart", fmt_num(len(df_rev)))
k2.metric("Confermate da legge", fmt_num(int(df_rev["confermata_da_legge"].sum())))
k3.metric("Con ≥1 DDL collegata", fmt_num(int((df_rev["n_ddl_collegate"] > 0).sum())))

df_show = df_rev.copy()
if "rev_data" in df_show.columns:
    df_show["rev_data"] = df_show["rev_data"].astype(str).str[:10]

st.dataframe(
    df_show[
        [
            c
            for c in (
                "rev_data",
                "rev_codice",
                "rev_titolo",
                "rev_tipo",
                "n_ddl_collegate",
                "n_ddl_ha_legge",
                "join_methods",
                "confermata_da_legge",
                "urn_camera",
            )
            if c in df_show.columns
        ]
    ].sort_values("rev_data", ascending=False),
    width="stretch",
    hide_index=True,
)

st.caption(
    "Dati: compose `iter_costituzionale` (open-politica DDL × revisioni locali). "
    "`ha_legge` solo su join ad alta confidenza."
)
