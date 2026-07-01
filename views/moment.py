# -*- coding: utf-8 -*-
"""
Moment — Static Pitch-Moment Balance & Control Authority
========================================================
1-DOF rotational counterpart to the Trim & Thrust analysis
(see Pitch_Moment_JOSELITO.py).

Sums component force × arm about the CG to get the net static pitching
moment, then checks whether differential motor thrust has enough authority
to trim it across the flight envelope.

Sign convention: arm from CG, +forward (nose); force +up; moment = force·arm,
positive = nose-up. Pitch control arm  d_arm = motor_arm · sin(quad_angle).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

G0 = 9.81
RED, GREEN, BLUE, PURPLE = "#c62828", "#2e7d32", "#1565c0", "#7b1fa2"


# ============================================================
# Physics
# ============================================================
def trim_thrust_curve(v_array, mass, rho, S, A, CL0, CD0, g=G0):
    """Invert v -> gamma along the trim curve and return T_trim(v), gamma(v)."""
    W = mass * g
    kL = 0.5 * rho * CL0 * S
    kD = 0.5 * rho * CD0 * A
    T = np.full_like(v_array, np.nan, dtype=float)
    gam = np.full_like(v_array, np.nan, dtype=float)
    for i, v in enumerate(v_array):
        cos_g = v ** 2 * kL / W
        if 0 < cos_g <= 1:
            gr = np.arccos(cos_g)
            L = kL * v ** 2
            D = kD * v ** 2
            T[i] = D + L * np.tan(gr)
            gam[i] = np.degrees(gr)
    return gam, T


# ============================================================
# Sidebar — configuration
# ============================================================
st.title("⚖️ Moment — Static Pitch-Moment Balance")
st.caption("Component force × arm about the CG → net pitching moment, and "
           "whether differential motor thrust can trim it. "
           "⚠️ Component loads are placeholders.")

with st.sidebar:
    st.header("Configuration")

    st.subheader("Propulsion & geometry")
    T_avail_total = st.number_input("Total available thrust [N]", 1.0, 1000.0,
                                    80.0, 1.0)
    motor_arm = st.number_input("Motor radial arm [m]", 0.001, 2.0, 0.100,
                                0.005, format="%.3f")
    quad_angle = st.number_input("Quad X half-angle [deg]", 1.0, 89.0, 45.0, 1.0)

    st.subheader("Vehicle (trim curve)")
    mass = st.number_input("Mass m [kg]", 0.1, 100.0, 5.0, 0.1)
    rho = st.number_input("Air density ρ [kg/m³]", 0.1, 2.0, 1.225, 0.001,
                          format="%.3f")
    S = st.number_input("Wing area S [m²]", 0.001, 5.0, 0.027, 0.001,
                        format="%.3f")
    A = st.number_input("Drag area A [m²]", 0.001, 5.0, 0.02, 0.001,
                        format="%.3f")
    CL0 = st.number_input("C_L0 [-]", 0.001, 2.5, 0.08, 0.01, format="%.3f")
    CD0 = st.number_input("C_D0 [-]", 0.001, 2.5, 0.4, 0.01, format="%.3f")

    st.subheader("Reference speeds")
    v_cruise = st.number_input("Cruise speed [m/s]", 1.0, 300.0, 60.0, 1.0)
    v_dash = st.number_input("Dash speed [m/s]", 1.0, 300.0, 90.0, 1.0)

d_arm = motor_arm * np.sin(np.radians(quad_angle))

# ---- Editable component moment table ----
st.subheader("Component moment table")
st.caption("Edit forces/arms, or add rows. Force +up, arm +forward (toward nose).")
default_components = pd.DataFrame({
    "Component": ["Payload", "Wing", "Electronics", "Tail", "Battery"],
    "Force [N]": [-4.91, 20.00, -7.85, 4.00, 14.00],
    "Arm [m]": [0.30, 0.10, 0.05, -0.15, -0.010],
})
edited = st.data_editor(default_components, num_rows="dynamic",
                        use_container_width=True, key="moment_table")

comp = edited.dropna(subset=["Force [N]", "Arm [m]"]).copy()
comp["Moment [N·m]"] = comp["Force [N]"] * comp["Arm [m]"]
M_net = float(comp["Moment [N·m]"].sum())
sense = "nose-up ↑" if M_net > 0 else ("nose-down ↓" if M_net < 0 else "balanced")
dT_trim_needed = abs(M_net) / (2 * d_arm)

# tail force for neutral balance (all else fixed)
tail_rows = comp[comp["Component"].str.lower() == "tail"]
F_tail_needed = None
if not tail_rows.empty and tail_rows.iloc[0]["Arm [m]"] != 0:
    tail_arm = tail_rows.iloc[0]["Arm [m]"]
    tail_moment = tail_rows.iloc[0]["Moment [N·m]"]
    F_tail_needed = -(M_net - tail_moment) / tail_arm

# ---- Header metrics ----
m1, m2, m3, m4 = st.columns(4)
m1.metric("Net moment M_net", f"{M_net:+.3f} N·m", help=sense)
m2.metric("Sense", sense)
m3.metric("Pitch control arm", f"{d_arm * 1000:.1f} mm")
m4.metric("ΔT to trim / pair", f"{dT_trim_needed:.2f} N")

# ============================================================
# Tabs
# ============================================================
tab_break, tab_auth, tab_contour = st.tabs(
    ["📊 Moment breakdown", "📈 Control authority", "🗺️ Authority map"])

# ---------- Moment breakdown ----------
with tab_break:
    names = comp["Component"].tolist() + ["NET"]
    moments = comp["Moment [N·m]"].tolist() + [M_net]
    colors = [RED if v < 0 else GREEN for v in moments[:-1]] + [BLUE]

    fig = go.Figure(go.Bar(
        x=names, y=moments, marker_color=colors,
        text=[f"{v:+.2f}" for v in moments], textposition="outside"))
    fig.add_hline(y=0, line=dict(color="black", width=1))
    fig.update_layout(
        height=460, title=f"Static pitch-moment balance — "
                          f"NET = {M_net:+.3f} N·m ({sense})",
        yaxis_title="Moment about CG [N·m]", showlegend=False,
        margin=dict(t=60))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        comp.style.format({"Force [N]": "{:.2f}", "Arm [m]": "{:.3f}",
                           "Moment [N·m]": "{:+.3f}"}),
        hide_index=True, use_container_width=True)

    if F_tail_needed is not None:
        cur = tail_rows.iloc[0]["Force [N]"]
        st.info(f"**Tail force for neutral balance** (all else fixed): "
                f"current {cur:+.2f} N → required **{F_tail_needed:+.2f} N** "
                f"(Δ {F_tail_needed - cur:+.2f} N).")

# ---------- Control authority vs speed ----------
with tab_auth:
    v_arr = np.linspace(10.0, float(v_dash), 200)
    _, T_trim = trim_thrust_curve(v_arr, mass, rho, S, A, CL0, CD0)
    dT_avail = (T_avail_total - T_trim) / 2
    dT_need = np.full_like(v_arr, dT_trim_needed)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=v_arr, y=dT_need, mode="lines",
                             name="ΔT needed (trim net moment)",
                             line=dict(color=RED, width=3)))
    fig.add_trace(go.Scatter(x=v_arr, y=dT_avail, mode="lines",
                             name="ΔT available (above trim)",
                             line=dict(color=GREEN, width=3)))
    # deficit shading where needed > available
    deficit_mask = dT_need > dT_avail
    fig.add_trace(go.Scatter(
        x=np.concatenate([v_arr, v_arr[::-1]]),
        y=np.concatenate([np.where(deficit_mask, dT_avail, dT_need),
                          np.where(deficit_mask, dT_need, dT_need)[::-1]]),
        fill="toself", fillcolor="rgba(198,40,40,0.12)",
        line=dict(width=0), hoverinfo="skip", showlegend=False))
    for vx, lab, col in [(v_cruise, "cruise", GREEN), (v_dash, "dash", RED)]:
        fig.add_vline(x=vx, line=dict(color=col, dash="dot"),
                      annotation_text=lab, annotation_position="top")
    fig.update_layout(
        height=500, title="Pitch control authority vs airspeed",
        xaxis_title="Airspeed v [m/s]",
        yaxis_title="Differential thrust per pair [N]",
        yaxis=dict(rangemode="tozero"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=70))
    st.plotly_chart(fig, use_container_width=True)

    # feasibility crossing at current M_net
    diff = dT_avail - dT_need
    idx = np.where(np.diff(np.sign(diff)) != 0)[0]
    if len(idx):
        i = idx[0]
        t = diff[i] / (diff[i] - diff[i + 1])
        v_cross = v_arr[i] + t * (v_arr[i + 1] - v_arr[i])
        st.warning(f"⚠️ Authority runs out at **v ≈ {v_cross:.1f} m/s** "
                   f"for the current |M_net| = {abs(M_net):.3f} N·m "
                   f"(above this speed, ΔT available < ΔT needed).")
    elif np.all(diff >= 0):
        st.success("✅ Sufficient differential-thrust authority across the "
                   "whole speed range for the current net moment.")
    else:
        st.error("❌ Insufficient authority across the whole speed range.")

# ---------- Authority contour ----------
with tab_contour:
    c1, c2 = st.columns([3, 1])
    with c2:
        M_max = st.number_input("Max |M_net| on map [N·m]", 0.1, 20.0, 3.0, 0.1)
        clip = st.slider("Deficit colour cap [N]", 1, 50, 15)

    v_arr = np.linspace(10.0, float(v_dash), 200)
    M_arr = np.linspace(0.0, float(M_max), 200)
    _, T_trim = trim_thrust_curve(v_arr, mass, rho, S, A, CL0, CD0)
    dT_avail_v = (T_avail_total - T_trim) / 2
    dT_need_M = M_arr / (2 * d_arm)
    deficit = dT_need_M[:, None] - dT_avail_v[None, :]      # (M, v)

    cfig = go.Figure()
    cfig.add_trace(go.Contour(
        x=v_arr, y=M_arr, z=np.clip(deficit, -clip, clip),
        colorscale="RdYlGn_r", zmid=0,
        colorbar=dict(title="ΔT deficit [N]"),
        contours=dict(showlines=False),
        hovertemplate="v=%{x:.1f} m/s<br>|M_net|=%{y:.2f} N·m<br>"
                      "deficit=%{z:.1f} N<extra></extra>"))
    # feasibility boundary (deficit = 0)
    cfig.add_trace(go.Contour(
        x=v_arr, y=M_arr, z=deficit, showscale=False,
        contours=dict(start=0, end=0, size=1, coloring="lines"),
        line=dict(color="black", width=2.5),
        name="feasibility boundary", hoverinfo="skip"))
    if 0 <= abs(M_net) <= M_max:
        cfig.add_hline(y=abs(M_net), line=dict(color=BLUE, width=2, dash="dash"),
                       annotation_text=f"current |M_net| = {abs(M_net):.3f} N·m",
                       annotation_position="top left")
    for vx, lab, col in [(v_cruise, "cruise", GREEN), (v_dash, "dash", PURPLE)]:
        cfig.add_vline(x=vx, line=dict(color=col, dash="dot"),
                       annotation_text=lab, annotation_position="bottom")
    cfig.update_layout(
        height=560, xaxis_title="Airspeed v [m/s]",
        yaxis_title="Net static pitch moment |M_net| [N·m]",
        title="Control-authority feasibility over (airspeed, net moment)",
        margin=dict(t=60))
    with c1:
        st.plotly_chart(cfig, use_container_width=True)
    st.caption("Red = insufficient differential-thrust authority, green = "
               "surplus, black line = feasibility boundary (ΔT deficit = 0). "
               "Read where the blue dashed current-moment line crosses the "
               "boundary to get the limiting airspeed.")
