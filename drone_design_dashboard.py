# -*- coding: utf-8 -*-
"""
Drone Design — multipage entry / router.

Modular layout: one file per dashboard in views/. To add a new analysis,
create views/<name>.py and add a single st.Page entry under "Analyses" below.

Run:
    streamlit run drone_design_dashboard.py
"""

import streamlit as st

st.set_page_config(page_title="Drone Design", page_icon="🚁", layout="wide")

pages = {
    "Overview": [
        st.Page("views/home.py", title="Home", icon="🏠", default=True),
    ],
    "Analyses": [
        st.Page("views/trim_thrust.py", title="Trim & Thrust", icon="🚁"),
        st.Page("views/trim_alpha.py", title="α-Trim", icon="📐"),
        st.Page("views/moment.py", title="Moment", icon="⚖️"),
        st.Page("views/propeller.py", title="Propeller", icon="🌀"),
        st.Page("views/weight.py", title="Weight & BOM", icon="📦"),
        st.Page("views/battery.py", title="Battery", icon="🔋"),
        # Add future analyses here, e.g.:
        # st.Page("views/transient.py", title="Transient", icon="⏱️"),
        # st.Page("views/cfd.py",       title="CFD",       icon="🌀"),
    ],
    "About": [
        st.Page("views/bio.py", title="Bio", icon="👤"),
    ],
}

st.navigation(pages).run()
