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
    "envelope. Each dashboard here covers one step of that iterative design "
    "loop — pick a step from the sidebar to explore it.")

st.subheader("Design workflow")

# Iterative loop:
#   1 Mission definition
#   2 Trim & Thrust · Moment · Transient   (the analysis stage)
#   3 Battery calculation
#   4 CFD
#   -> repeat step 2
workflow_dot = r"""
digraph G {
    rankdir=LR;
    bgcolor="transparent";
    node [shape=box, style="rounded,filled", fontname="Helvetica",
          fontsize=11, margin="0.18,0.11", color="#607d8b", penwidth=1.2];
    edge [color="#546e7a", arrowsize=0.8, penwidth=1.2];

    mission [label="1 · Mission\ndefinition\na.flight time\nb.Cruise speed\nmax_speed", fillcolor="#e3f2fd"];

    subgraph cluster_step2 {
        label="2 · Steady & dynamic analysis";
        labeljust="l"; fontname="Helvetica"; fontsize=11; fontcolor="#37474f";
        style="rounded,dashed"; color="#90a4ae"; margin=12;
        trim      [label="Trim & Thrust  ✓", fillcolor="#c8e6c9"];
        moment    [label="Moment  ✓", fillcolor="#c8e6c9"];
        transient [label="Transient", fillcolor="#fff9c4"];
    }

    battery [label="3 · Battery\ncalculation", fillcolor="#ffe0b2"];
    cfd     [label="4 · CFD", fillcolor="#f8bbd0"];

    mission -> trim;
    mission -> moment;
    mission -> transient;

    trim      -> battery;
    moment    -> battery;
    transient -> battery;

    battery -> cfd;

    cfd -> trim [label="  repeat step 2  ", style="dashed",
                 constraint=false, color="#c62828", fontcolor="#c62828",
                 fontsize=10];
}
"""
st.graphviz_chart(workflow_dot, use_container_width=True)

st.caption(
    "🟢 Available now · 🟡 Planned.  The loop iterates: refined CFD results "
    "feed back into the trim / moment / transient analyses until the design "
    "converges.")

st.divider()

st.subheader("Analyses")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**🚁 Trim & Thrust**  🟢")
    st.caption("Longitudinal steady-trim speed and required thrust vs pitch "
               "angle; thrust-feasibility envelope.")
with c2:
    st.markdown("**⚖️ Moment**  🟢")
    st.caption("Static pitch-moment balance about the CG and differential-"
               "thrust control authority.")
with c3:
    st.markdown("**⏱️ Transient · 🔋 Battery · 🌀 CFD**  🟡")
    st.caption("Transition dynamics, energy/endurance sizing and "
               "high-fidelity aerodynamics (planned).")
