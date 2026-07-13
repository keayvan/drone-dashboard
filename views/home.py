# -*- coding: utf-8 -*-
"""Home — project overview and the iterative design workflow."""

from pathlib import Path
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

st.subheader("The design process")
_wf = Path(__file__).resolve().parent.parent / "assets" / "workflow-simple.svg"
if _wf.exists():
    st.markdown(
        '<div style="display:flex;justify-content:center;margin:.4rem 0 .4rem">'
        '<div style="max-width:520px;width:100%">'
        + _wf.read_text(encoding="utf-8") + '</div></div>',
        unsafe_allow_html=True)
st.caption("A closed-loop conceptual design process — sizing, aerodynamics, "
           "propulsion, dynamics and control, iterated to convergence.")

st.divider()
st.subheader("Explore the tools")


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

    # ---- CFD (offered as a service) ----
    with st.container(border=True):
        st.markdown("#### 💨 CFD — I do this part for you  🤝")
        st.markdown(
            "Use the dashboards above to size your drone yourself in minutes. "
            "When you're ready to **verify and refine** the design with "
            "high-fidelity CFD — drag polars, transition & stability, "
            "propeller / duct flow, thermal — I deliver it as a **consulting "
            "service** and feed the results back into your sizing.")
        b = st.columns(3)
        b[0].link_button(
            "📧 Request a CFD quote",
            "mailto:keayvan.keramati@gmail.com?subject=CFD%20project%20enquiry",
            use_container_width=True)
        b[1].link_button("🔗 LinkedIn",
                         "https://linkedin.com/in/keayvan-keramati",
                         use_container_width=True)
        b[2].page_link("views/bio.py", label="👤 About me",
                       use_container_width=True)

    st.caption("↩ CFD results feed back into **Flight Dynamics** — iterate "
               "until the design converges.  🟢 available now · 🟡 planned · "
               "🤝 done for you")

st.divider()
with st.container(border=True):
    st.markdown("### 🤝 Design it here — I'll verify it with CFD")
    st.markdown(
        "These tools give you a solid **preliminary drone design** for free. "
        "For production-grade **CFD and detailed aerodynamic design**, work "
        "with me — a PhD mechanical engineer with 10+ years in aerodynamics, "
        "propulsion and UAV design.")
    cc = st.columns(3)
    cc[0].link_button(
        "📧 Start a project",
        "mailto:keayvan.keramati@gmail.com?subject=Drone%20CFD%20project",
        use_container_width=True)
    cc[1].link_button("🔗 LinkedIn",
                      "https://linkedin.com/in/keayvan-keramati",
                      use_container_width=True)
    cc[2].page_link("views/bio.py", label="👤 About / credentials",
                    use_container_width=True)
