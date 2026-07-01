# -*- coding: utf-8 -*-
"""About Me page — profile of the author."""

from pathlib import Path
import streamlit as st

PHOTO = Path(__file__).resolve().parent.parent / "assets" / "profile.png"

# ---- Header: photo + name/title ----
col_img, col_txt = st.columns([1, 2.4], gap="large")

with col_img:
    if PHOTO.exists():
        st.image(str(PHOTO), width=240)
    else:
        st.info("Profile photo not found.")

with col_txt:
    st.title("Keayvan Keramati")
    st.markdown(
        "**PhD Mechanical Engineer** &nbsp;·&nbsp; Multi-Sector R&D  \n"
        "Aerodynamics · Propulsion · Robotics · Digital Twin & AI-Driven Simulation")
    st.markdown(
        "📧 [keayvan.keramati@gmail.com](mailto:keayvan.keramati@gmail.com) "
        "&nbsp;|&nbsp; "
        "🔗 [LinkedIn](https://linkedin.com/in/keayvan-keramati)")

st.divider()

# ---- Profile ----
st.subheader("Profile")
st.markdown(
    "PhD Mechanical Engineer with **10+ years of cross-sector R&D experience** "
    "spanning aerospace, automotive, energy, robotics, and advanced "
    "manufacturing. I deliver complex engineering projects end-to-end — from "
    "concept and high-fidelity CFD modeling through actuator and control-system "
    "design, system integration, experimental validation, and performance "
    "optimization. My work combines deep expertise in aerodynamics, propulsion, "
    "robotics, and multi-physics simulation with modern Digital Twin and "
    "AI-driven methods.")

# ---- Highlights + expertise ----
c1, c2 = st.columns(2, gap="large")

with c1:
    st.subheader("Technical highlights")
    st.markdown(
        "- ~**30 %** gain in UAV propulsion efficiency & flight time\n"
        "- Designed in-house **BLDC motors & actuators** for robotics\n"
        "- Built a **Digital Twin** framework with PINNs for defect prediction\n"
        "- **2 registered patents** · 9 journal/book papers · 2 conferences\n"
        "- 10+ years multi-sector R&D across 4 industries")

with c2:
    st.subheader("Core expertise")
    st.markdown(
        "- Aerodynamics, CFD & multi-physics simulation\n"
        "- Propulsion & powertrain systems\n"
        "- UAV systems design, integration & flight testing\n"
        "- Robotics, actuators & BLDC motor design\n"
        "- Control systems & dynamic modeling\n"
        "- Digital Twin & AI-driven engineering")

# ---- Tools ----
st.subheader("Selected tools")
st.markdown(
    "ANSYS Fluent · OpenFOAM · Siemens NX · CATIA · SolidWorks · "
    "Python (NumPy/SciPy/Pandas) · PyTorch · TensorFlow · MATLAB · C++ · "
    "PX4 · ArduPilot · ROS2")

st.caption("This drone-design dashboard is one of my engineering side projects. "
           "Use the sidebar to return to the dashboard.")
