#!/usr/bin/env python3
"""
Costituzione Italiana · Dashboard Streamlit
139 articoli, 22k pronunce, 266k massime, 16k citazioni — la Costituzione come non l'hai mai vista.
"""

import streamlit as st
from lab_connectors.branding import apply_branding

st.set_page_config(
    page_title="Costituzione Italiana · Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_branding(
    repo_name="costituzione-italiana",
    repo_url="https://github.com/dataciviclab/costituzione-italiana",
)

pages = {
    "": [
        st.Page("pages/01_Panoramica.py", title="Panoramica", icon="📊", default=True),
    ],
    "Esplora": [
        st.Page("pages/02_Articolo.py", title="Articolo", icon="📜"),
        st.Page("pages/03_Giurisprudenza.py", title="Giurisprudenza", icon="⚖️"),
    ],
    "Corte Costituzionale": [
        st.Page("pages/06_Pronunce.py", title="Pronunce", icon="📋"),
        st.Page("pages/08_Giudici.py", title="Giudici", icon="🏛️"),
        st.Page("pages/09_Sentenze.py", title="Sentenze Complete", icon="⚡"),
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

pg.run()
