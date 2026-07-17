# -*- coding: utf-8 -*-
"""
Wing & Power Loading — fixed-wing sizing
========================================
Turn a weight estimate into the two parameters that size the airframe:

  Wing loading   W/S = ½·ρ·V_stall²·C_Lmax        → wing area  S = W/(W/S)
  Power loading  W/P = W / P_required

The power required is set by the more demanding of cruise or climb:
  P = ( D·V_cruise + W·ROC ) / η_prop

A matching (constraint) chart plots the required power loading against wing
loading, with the stall limit and the design point.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

G0 = 9.81
RED, BLUE, GREEN, ORANGE = "#e05252", "#4a9eff", "#3fb27f", "#e6902e"

st.title("🪁 Wing & Power Loading")
st.caption(
    "From an all-up weight, derive wing loading (W/S), wing area, power loading "
    "(W/P) and the required power — with a constraint matching chart.")

# Gray section boxes (match the Weight & BOM page).
st.markdown(
    """
    <style>
    [class*="st-key-lbox"] {
        background: #2b2f37 !important;
        border: 1px solid #3c414a !important;
        border-radius: 12px !important;
        padding: 0.75rem 0.9rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True)

results_area = st.container()

st.subheader("Inputs")
c1, c2, c3, c4 = st.columns(4)

with c1:
    with st.container(border=True, key="lbox_wair"):
        st.markdown("**Weight & air**")
        m = st.number_input("All-up mass m [kg]", 0.1, 500.0, 3.0, 0.1)
        rho = st.number_input("Air density ρ [kg/m³]", 0.3, 1.5, 1.225, 0.001,
                              format="%.3f")

with c2:
    with st.container(border=True, key="lbox_stall"):
        st.markdown("**Low speed (stall)**")
        v_stall = st.number_input("Stall / min speed V_stall [m/s]", 3.0, 60.0,
                                  12.0, 0.5)
        clmax = st.number_input("Max lift coeff. C_Lmax", 0.6, 2.2, 1.2, 0.05)

with c3:
    with st.container(border=True, key="lbox_cruise"):
        st.markdown("**Cruise & climb**")
        v_cruise = st.number_input("Cruise speed V_cruise [m/s]", 5.0, 120.0,
                                   18.0, 0.5)
        roc = st.number_input("Rate of climb ROC [m/s]", 0.0, 30.0, 3.0, 0.5)
        eta = st.slider("Propeller efficiency η", 0.30, 0.85, 0.60, 0.01)

with c4:
    with st.container(border=True, key="lbox_aero"):
        st.markdown("**Aerodynamics**")
        AR = st.number_input("Aspect ratio AR", 3.0, 25.0, 8.0, 0.5)
        cd0 = st.number_input("Zero-lift drag C_D0", 0.010, 0.100, 0.030, 0.001,
                              format="%.3f")
        e = st.slider("Oswald efficiency e", 0.60, 0.95, 0.80, 0.01)

# --------------------------------------------------------------------------
# Sizing
# --------------------------------------------------------------------------
W = m * G0                                    # weight [N]
ws_stall = 0.5 * rho * v_stall ** 2 * clmax   # max allowable wing loading [N/m²]
S = W / ws_stall                              # wing area [m²]
b = np.sqrt(AR * S)                           # span [m]
k = 1.0 / (np.pi * e * AR)                    # induced-drag factor


def pw_cruise(ws):
    """Required power-to-weight for steady level flight at V_cruise."""
    return (0.5 * rho * v_cruise ** 3 * cd0 / ws
            + ws * k / (0.5 * rho * v_cruise)) / eta


def pw_climb(ws):
    """Cruise power plus the extra to climb at ROC."""
    return pw_cruise(ws) + roc / eta


# Design point = stall-limited wing loading; power sized by climb.
pw_design = pw_climb(ws_stall)
P_req = pw_design * W                          # required power [W]
wp = 1.0 / pw_design                           # power loading [N/W]

cl_cruise = W / (0.5 * rho * v_cruise ** 2 * S)
cd_cruise = cd0 + cl_cruise ** 2 * k
D_cruise = 0.5 * rho * v_cruise ** 2 * S * cd_cruise

with results_area:
    st.subheader("Results")
    with st.container(border=True, key="lbox_results"):
        r = st.columns(4)
        r[0].metric("Wing loading W/S", f"{ws_stall:,.1f} N/m²",
                    help=f"{ws_stall / G0:,.1f} kg/m². "
                         f"Set by stall: ½·ρ·V_stall²·C_Lmax.")
        r[1].metric("Wing area S", f"{S:,.3f} m²",
                    help=f"Span ≈ {b:,.2f} m at AR = {AR:g}.")
        r[2].metric("Power loading W/P", f"{wp:,.3f} N/W",
                    help=f"{P_req / m:,.0f} W/kg installed.")
        r[3].metric("Power required", f"{P_req:,.0f} W",
                    help=f"Cruise ≈ {D_cruise * v_cruise / eta:,.0f} W; "
                         f"remainder is climb.")
    st.caption(f"Cruise check → C_L = {cl_cruise:.2f}, C_D = {cd_cruise:.3f}, "
               f"drag ≈ {D_cruise:.1f} N at {v_cruise:g} m/s.")
    if cl_cruise > clmax:
        st.error("Cruise C_L exceeds C_Lmax — the wing can't fly this fast "
                 "with this area. Increase area (lower W/S) or speed.")
    st.divider()

# --------------------------------------------------------------------------
# Matching (constraint) chart
# --------------------------------------------------------------------------
st.subheader("Constraint matching chart")
st.caption("Required power loading vs wing loading. Feasible designs lie ABOVE "
           "the curves and LEFT of the stall line. The dot is the design point.")

ws_grid = np.linspace(ws_stall * 0.35, ws_stall * 1.25, 200)
fig = go.Figure()
fig.add_trace(go.Scatter(x=ws_grid, y=pw_cruise(ws_grid), name="Cruise",
                         line=dict(color=BLUE, width=3)))
fig.add_trace(go.Scatter(x=ws_grid, y=pw_climb(ws_grid), name="Climb",
                         line=dict(color=ORANGE, width=3)))
fig.add_vline(x=ws_stall, line=dict(color=RED, width=2, dash="dash"),
              annotation_text="Stall limit", annotation_position="top left")
fig.add_trace(go.Scatter(x=[ws_stall], y=[pw_design], name="Design point",
                         mode="markers",
                         marker=dict(color=GREEN, size=14, symbol="circle",
                                     line=dict(color="white", width=1.5))))
fig.update_layout(
    xaxis_title="Wing loading  W/S  [N/m²]",
    yaxis_title="Power loading req.  P/W  [W/N]",
    template="plotly_dark", height=460,
    legend=dict(orientation="h", y=1.08),
    margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig, use_container_width=True)

st.divider()
with st.expander("📖 The physics"):
    st.markdown(
        r"""
**Wing loading** comes from the slowest speed you must still fly. At stall,
lift equals weight with the wing at maximum lift coefficient:

$$W = \tfrac{1}{2}\,\rho\,V_\text{stall}^2\,S\,C_{L\max}
\;\Rightarrow\; \frac{W}{S} = \tfrac{1}{2}\,\rho\,V_\text{stall}^2\,C_{L\max}$$

The wing area then follows directly: $S = W / (W/S)$.

**Power loading** is set by the power the propulsion must deliver. In steady
cruise thrust equals drag, and climbing adds $W\cdot ROC$ of work rate:

$$P = \frac{D\,V_\text{cruise} + W\cdot ROC}{\eta_\text{prop}},
\qquad \frac{W}{P} = \frac{W}{P}$$

Drag uses a parabolic polar $C_D = C_{D0} + \dfrac{C_L^2}{\pi e\,AR}$.

Lower **W/S** → bigger wings, slower, short takeoff, gust-sensitive.
Higher **W/S** → smaller wings, faster, efficient cruise, higher stall speed.
        """)
