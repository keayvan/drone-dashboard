# -*- coding: utf-8 -*-
"""Home — project overview and the iterative design workflow."""

import streamlit as st

st.title("🚁 Drone Design — Overview")

st.markdown(
    "This is an engineering workbench for a **tail-sitter VTOL drone** — an "
    "aircraft that takes off and lands **vertically** (hovering with the "
    "fuselage upright, pitch angle γ = 90°) and tilts over to fly efficiently "
    "at **high speed in forward cruise** (γ → 0°).\n\n"
    "Designing such a vehicle means balancing **lift, drag, thrust, weight, "
    "control moments, energy and aerodynamics** across the whole flight "
    "envelope. The workflow below runs the loop — click any analysis to open "
    "its dashboard.")

st.subheader("Design workflow")


def _arrow():
    st.markdown(
        "<div style='text-align:center;font-size:1.5rem;color:#90a4ae;"
        "line-height:1.1'>↓</div>", unsafe_allow_html=True)


outer = st.columns([1, 6, 1])
with outer[1]:

    # ---- Mission ----
    with st.container(border=True):
        st.markdown("#### 🎯 Mission")
        st.caption("Targets that define the design point")
        mc = st.columns(3)
        mc[0].markdown("⏱️ **Flight time**")
        mc[1].markdown("🚀 **Cruise speed**")
        mc[2].markdown("⚡ **Max speed**")

    _arrow()

    # ---- Flight Dynamics (linked dashboards) ----
    with st.container(border=True):
        st.markdown("#### 🛩️ Flight Dynamics")
        st.caption("Steady & dynamic analyses — click to open 🟢")
        fc = st.columns(5)
        fc[0].page_link("views/trim_thrust.py", label="Trim & Thrust",
                        icon="🚁", use_container_width=True)
        fc[1].page_link("views/trim_alpha.py", label="α-Trim", icon="📐",
                        use_container_width=True)
        fc[2].page_link("views/moment.py", label="Moment", icon="⚖️",
                        use_container_width=True)
        fc[3].page_link("views/propeller.py", label="Propeller", icon="🌀",
                        use_container_width=True)
        fc[4].page_link("views/battery.py", label="Battery", icon="🔋",
                        use_container_width=True)

    _arrow()

    # ---- Purchase components ----
    with st.container(border=True):
        st.markdown("#### 🛒 Purchase components  🟡")
        st.caption("Select motors, ESCs, cells and airframe from the sizing "
                   "above (planned).")

    _arrow()

    # ---- CFD ----
    with st.container(border=True):
        st.markdown("#### 💨 CFD  🟡")
        st.caption("High-fidelity aerodynamic verification (planned).")

    st.caption("↩ CFD results feed back into **Flight Dynamics** — iterate "
               "until the design converges.  🟢 available · 🟡 planned")
