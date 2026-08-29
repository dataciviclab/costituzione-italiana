#!/usr/bin/env python3
"""
Costituzione Italiana · Dashboard Streamlit
139 articoli, 50 revisioni, 266k massime, 16k citazioni — la Costituzione come non l'hai mai vista.
"""

import streamlit as st

st.set_page_config(
    page_title="Costituzione Italiana · Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = {
    "": [
        st.Page("pages/01_Panoramica.py", title="Panoramica", icon="📊", default=True),
    ],
    "Esplora": [
        st.Page("pages/02_Articolo.py", title="Articolo", icon="📜"),
        st.Page("pages/03_Giurisprudenza.py", title="Giurisprudenza", icon="⚖️"),
    ],
    "Dati": [
        st.Page("pages/04_Revisioni.py", title="Revisioni", icon="🔧"),
        st.Page("pages/05_Citazioni.py", title="Citazioni", icon="📝"),
    ],
    "Strumenti": [
        st.Page("pages/07_SQL.py", title="Query SQL", icon="🧪"),
    ],
}

pg = st.navigation(pages, position="sidebar")

st.sidebar.markdown("---")
st.sidebar.caption("Dati: [costituzione-italiana](https://github.com/dataciviclab/costituzione-italiana)")
st.sidebar.caption("Codice: [dataciviclab/costituzione-italiana](https://github.com/dataciviclab/costituzione-italiana)")
st.sidebar.caption("[DataCivicLab](https://dataciviclab.org/) · CC BY 4.0")

pg.run()
