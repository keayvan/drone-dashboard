# -*- coding: utf-8 -*-
"""
Drone Design Dashboard — multipage entry / router.

Defines the sidebar navigation and hands off to the individual page scripts
in views/. Run:
    streamlit run drone_design_dashboard.py
"""

import streamlit as st

st.set_page_config(page_title="Drone Design", page_icon="🚁", layout="wide")

pages = [
    st.Page("views/dashboard.py", title="Dashboard", icon="🚁", default=True),
    st.Page("views/bio.py", title="Bio", icon="👤"),
]

st.navigation(pages).run()
