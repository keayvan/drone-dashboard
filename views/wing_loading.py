# -*- coding: utf-8 -*-
"""
Wing & Power Loading — fixed-wing and VTOL sizing
=================================================
Two sizing regimes in separate tabs:

Fixed wing
  Wing loading   W/S = ½·ρ·V_stall²·C_Lmax     → wing area  S = W/(W/S)
  Power loading  W/P = W / P,  P = (D·V_cruise + W·ROC)/η_prop
  → sized by cruise/climb.

VTOL
  Hover thrust   T = (T/W)·W                    (T/W ≥ 1 for lift-off + control)
  Hover power    P_hover = Σ  T_rotor^1.5 / (FM·√(2·ρ·A_rotor))   (momentum theory)
  Installed power = max(P_hover, P_cruise)      → almost always hover-driven.

The Physics tab derives both.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

G0 = 9.81
RED, BLUE, GREEN, ORANGE = "#e05252", "#4a9eff", "#3fb27f", "#e6902e"

st.title("🪁 Wing & Power Loading")
st.caption(
    "Size the airframe from an all-up weight — for a fixed-wing UAV (sized by "
    "cruise/climb) or a VTOL (sized by hover).")

# Gray section boxes.
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


def parabolic_drag(W, rho, V, S, cd0, k):
    """Return (C_L, C_D, drag) at speed V for wing area S."""
    cl = W / (0.5 * rho * V ** 2 * S)
    cd = cd0 + cl ** 2 * k
    D = 0.5 * rho * V ** 2 * S * cd
    return cl, cd, D


tab_fw, tab_vtol, tab_phys = st.tabs(
    ["✈️ Fixed wing", "🚁 VTOL", "📖 Physics"])

# ==========================================================================
# FIXED WING
# ==========================================================================
with tab_fw:
    fw_results = st.container()

    st.subheader("Inputs")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True, key="lbox_fw_wair"):
            st.markdown("**Weight & air**")
            m = st.number_input("All-up mass m [kg]", 0.1, 500.0, 3.0, 0.1,
                                key="fw_m")
            rho = st.number_input("Air density ρ [kg/m³]", 0.3, 1.5, 1.225,
                                  0.001, format="%.3f", key="fw_rho")
    with c2:
        with st.container(border=True, key="lbox_fw_stall"):
            st.markdown("**Low speed (stall)**")
            v_stall = st.number_input("Stall / min speed V_stall [m/s]", 3.0,
                                      60.0, 12.0, 0.5, key="fw_vstall")
            clmax = st.number_input("Max lift coeff. C_Lmax", 0.6, 2.2, 1.2,
                                    0.05, key="fw_clmax")
    with c3:
        with st.container(border=True, key="lbox_fw_cruise"):
            st.markdown("**Cruise & climb**")
            v_cruise = st.number_input("Cruise speed V_cruise [m/s]", 5.0,
                                       120.0, 18.0, 0.5, key="fw_vcru")
            roc = st.number_input("Rate of climb ROC [m/s]", 0.0, 30.0, 3.0,
                                  0.5, key="fw_roc")
            eta = st.slider("Propeller efficiency η", 0.30, 0.85, 0.60, 0.01,
                            key="fw_eta")
    with c4:
        with st.container(border=True, key="lbox_fw_aero"):
            st.markdown("**Aerodynamics**")
            AR = st.number_input("Aspect ratio AR", 3.0, 25.0, 8.0, 0.5,
                                 key="fw_ar")
            cd0 = st.number_input("Zero-lift drag C_D0", 0.010, 0.100, 0.030,
                                  0.001, format="%.3f", key="fw_cd0")
            e = st.slider("Oswald efficiency e", 0.60, 0.95, 0.80, 0.01,
                          key="fw_e")

    W = m * G0
    ws_stall = 0.5 * rho * v_stall ** 2 * clmax
    S = W / ws_stall
    b = np.sqrt(AR * S)
    k = 1.0 / (np.pi * e * AR)

    def pw_cruise(ws):
        return (0.5 * rho * v_cruise ** 3 * cd0 / ws
                + ws * k / (0.5 * rho * v_cruise)) / eta

    def pw_climb(ws):
        return pw_cruise(ws) + roc / eta

    pw_design = pw_climb(ws_stall)
    P_req = pw_design * W
    wp = 1.0 / pw_design
    cl_c, cd_c, D_c = parabolic_drag(W, rho, v_cruise, S, cd0, k)

    with fw_results:
        st.subheader("Results")
        with st.container(border=True, key="lbox_fw_results"):
            r = st.columns(4)
            r[0].metric("Wing loading W/S", f"{ws_stall:,.1f} N/m²",
                        help=f"{ws_stall / G0:,.1f} kg/m². "
                             f"½·ρ·V_stall²·C_Lmax.")
            r[1].metric("Wing area S", f"{S:,.3f} m²",
                        help=f"Span ≈ {b:,.2f} m at AR = {AR:g}.")
            r[2].metric("Power loading W/P", f"{wp:,.3f} N/W",
                        help=f"{P_req / m:,.0f} W/kg installed.")
            r[3].metric("Power required", f"{P_req:,.0f} W",
                        help=f"Cruise ≈ {D_c * v_cruise / eta:,.0f} W; rest is "
                             f"climb.")
        st.caption(f"Cruise check → C_L = {cl_c:.2f}, C_D = {cd_c:.3f}, drag ≈ "
                   f"{D_c:.1f} N at {v_cruise:g} m/s.")
        if cl_c > clmax:
            st.error("Cruise C_L exceeds C_Lmax — increase area (lower W/S) or "
                     "speed.")
        st.divider()

    st.subheader("📈 Constraint matching chart")
    st.caption("Required power loading vs wing loading. Feasible designs lie "
               "ABOVE the curves and LEFT of the stall line.")
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
                             marker=dict(color=GREEN, size=14,
                                         line=dict(color="white", width=1.5))))
    fig.update_layout(
        xaxis_title="Wing loading  W/S  [N/m²]",
        yaxis_title="Power loading req.  P/W  [W/N]",
        template="plotly_dark", height=440,
        legend=dict(orientation="h", y=1.08),
        margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True, key="fw_chart")

# ==========================================================================
# VTOL
# ==========================================================================
with tab_vtol:
    v_results = st.container()

    st.subheader("Inputs")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        with st.container(border=True, key="lbox_v_wair"):
            st.markdown("**Weight & air**")
            vm = st.number_input("All-up mass m [kg]", 0.1, 500.0, 3.0, 0.1,
                                 key="v_m")
            vrho = st.number_input("Air density ρ [kg/m³]", 0.3, 1.5, 1.225,
                                   0.001, format="%.3f", key="v_rho")
    with d2:
        with st.container(border=True, key="lbox_v_hover"):
            st.markdown("**Hover (rotors)**")
            Drot = st.number_input("Rotor diameter D [m]", 0.05, 3.0, 0.30,
                                   0.01, key="v_d")
            Nrot = st.number_input("Number of rotors N", 1, 16, 4, 1, key="v_n")
            FM = st.slider("Figure of merit FM", 0.40, 0.80, 0.60, 0.01,
                           key="v_fm")
            TW = st.slider("Hover thrust-to-weight T/W", 1.0, 2.5, 1.5, 0.05,
                           key="v_tw")
    with d3:
        with st.container(border=True, key="lbox_v_fwd"):
            st.markdown("**Forward flight**")
            v_trans = st.number_input("Transition / min speed [m/s]", 3.0, 60.0,
                                      13.0, 0.5, key="v_vtrans")
            v_clmax = st.number_input("Max lift coeff. C_Lmax", 0.6, 2.2, 1.2,
                                      0.05, key="v_clmax")
            v_vcru = st.number_input("Cruise speed V_cruise [m/s]", 5.0, 120.0,
                                     20.0, 0.5, key="v_vcru")
            v_eta = st.slider("Prop efficiency η (cruise)", 0.30, 0.85, 0.60,
                              0.01, key="v_eta")
    with d4:
        with st.container(border=True, key="lbox_v_aero"):
            st.markdown("**Aerodynamics**")
            v_AR = st.number_input("Aspect ratio AR", 3.0, 25.0, 7.0, 0.5,
                                   key="v_ar")
            v_cd0 = st.number_input("Zero-lift drag C_D0", 0.010, 0.100, 0.035,
                                    0.001, format="%.3f", key="v_cd0")
            v_e = st.slider("Oswald efficiency e", 0.60, 0.95, 0.80, 0.01,
                            key="v_e")

    Wv = vm * G0
    k_v = 1.0 / (np.pi * v_e * v_AR)

    # --- Hover (momentum theory) ---
    T_total = TW * Wv                       # total hover thrust [N]
    T_rotor = T_total / Nrot
    A_rotor = np.pi * (Drot / 2) ** 2
    A_total = Nrot * A_rotor
    disk_loading = T_total / A_total         # [N/m²]

    def hover_power(D):
        Ar = np.pi * (D / 2) ** 2
        return Nrot * T_rotor ** 1.5 / (FM * np.sqrt(2 * vrho * Ar))

    P_hover = hover_power(Drot)

    # --- Forward flight (wing + cruise power) ---
    ws_v = 0.5 * vrho * v_trans ** 2 * v_clmax
    S_v = Wv / ws_v
    cl_v, cd_v, D_v = parabolic_drag(Wv, vrho, v_vcru, S_v, v_cd0, k_v)
    P_cruise_v = D_v * v_vcru / v_eta
    P_installed = max(P_hover, P_cruise_v)

    with v_results:
        st.subheader("Results")
        with st.container(border=True, key="lbox_v_results"):
            r = st.columns(4)
            r[0].metric("Hover thrust (T/W)", f"{T_total:,.0f} N",
                        help=f"{T_rotor:,.0f} N per rotor across {Nrot} rotors.")
            r[1].metric("Disk loading", f"{disk_loading:,.0f} N/m²",
                        help=f"{disk_loading / G0:,.1f} kg/m². Lower = less "
                             f"hover power.")
            r[2].metric("Hover power", f"{P_hover:,.0f} W",
                        help=f"{P_hover / vm:,.0f} W/kg (momentum theory).")
            r[3].metric("Installed power", f"{P_installed:,.0f} W",
                        help=f"max(hover {P_hover:,.0f} W, cruise "
                             f"{P_cruise_v:,.0f} W).")
        driver = "hover" if P_hover >= P_cruise_v else "cruise"
        st.caption(f"Sizing driver: **{driver}**.  Wing: W/S = {ws_v:,.1f} N/m² "
                   f"→ S = {S_v:,.3f} m².  Cruise power ≈ {P_cruise_v:,.0f} W.")
        st.divider()

    st.subheader("📈 Hover power vs rotor size")
    st.caption("Bigger rotors (lower disk loading) cut hover power sharply — the "
               "dominant lever for VTOL endurance.")
    d_grid = np.linspace(Drot * 0.5, Drot * 1.8, 200)
    figv = go.Figure()
    figv.add_trace(go.Scatter(x=d_grid, y=hover_power(d_grid), name="Hover power",
                              line=dict(color=BLUE, width=3)))
    figv.add_hline(y=P_cruise_v, line=dict(color=ORANGE, width=2, dash="dot"),
                   annotation_text="Cruise power", annotation_position="top right")
    figv.add_trace(go.Scatter(x=[Drot], y=[P_hover], name="Design point",
                              mode="markers",
                              marker=dict(color=GREEN, size=14,
                                          line=dict(color="white", width=1.5))))
    figv.update_layout(
        xaxis_title="Rotor diameter  D  [m]",
        yaxis_title="Power  [W]",
        template="plotly_dark", height=440,
        legend=dict(orientation="h", y=1.08),
        margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(figv, use_container_width=True, key="v_chart")

# ==========================================================================
# PHYSICS
# ==========================================================================
with tab_phys:
    st.markdown("### ✈️ Fixed wing")
    st.markdown("**Wing loading (W/S)** comes from the slowest speed you must "
                "still fly. At stall, lift equals weight at maximum lift "
                "coefficient:")
    st.latex(r"W = \tfrac{1}{2}\,\rho\,V_\text{stall}^2\,S\,C_{L\max}"
             r"\;\Rightarrow\; \frac{W}{S} = \tfrac{1}{2}\,\rho\,V_\text{stall}^2"
             r"\,C_{L\max}, \qquad S = \frac{W}{\,W/S\,}")
    st.markdown("**Power loading (W/P)** is set by cruise plus climb; thrust "
                "equals drag in steady flight, climbing adds $W\\cdot ROC$:")
    st.latex(r"P = \frac{D\,V_\text{cruise} + W\cdot ROC}{\eta_\text{prop}},"
             r"\qquad C_D = C_{D0} + \frac{C_L^2}{\pi\,e\,AR}")
    st.info("Lower **W/S** → bigger wings, slower, gust-sensitive.  \n"
            "Higher **W/S** → smaller wings, faster, efficient cruise.")

    st.divider()

    st.markdown("### 🚁 VTOL")
    st.markdown("A VTOL never lands on its wing, so **W/S** is set by the "
                "*transition* speed (not landing) and can be higher. The power, "
                "though, is set by **hover**, not cruise.")
    st.markdown("Hover needs **thrust greater than weight** for lift-off and "
                "control authority:")
    st.latex(r"T = (T/W)\cdot W, \qquad T/W \approx 1.2\text{–}2.0")
    st.markdown("Hover power follows **momentum (actuator-disk) theory** — with "
                "disk area $A=\\pi D^2/4$ per rotor and figure of merit FM:")
    st.latex(r"P_\text{hover} = \sum_i \frac{T_i^{\,1.5}}"
             r"{FM\,\sqrt{2\,\rho\,A_i}}, \qquad "
             r"\text{disk loading} = \frac{T}{A}")
    st.markdown("The installed power must cover the harder of the two regimes:")
    st.latex(r"P_\text{installed} = \max\!\left(P_\text{hover},\,"
             r"P_\text{cruise}\right)")
    st.info("Lower **disk loading** (bigger rotors) → much lower hover power and "
            "longer endurance. For most VTOLs, hover — not cruise — sizes the "
            "motors, ESCs and battery.")
