# -*- coding: utf-8 -*-
"""
Propeller — Diameter & Pitch Sizing
===================================
Sizes propeller diameter and pitch from the wanted drone speed, the available
thrust per prop, and the motor RPM (see propeller_calculation.py).

Model
-----
Thrust coefficient (static):  T = C_T · ρ · n² · D⁴      (n = RPM/60 [rev/s])
    → Diameter:   D = (T / (C_T·ρ·n²))^¼
Pitch speed (no-slip advance): V_pitch = pitch · n
    Slip = 1 − V / V_pitch   →   V_pitch = V / (1 − slip)
    → Pitch:      pitch = V_pitch / n = V / ((1 − slip)·n)
Advance ratio J = V / (n·D);   P/D = pitch/D = J / (1 − slip)
Tip speed = π·D·n  (keep tip Mach ≲ 0.7).
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

M2IN = 39.3701
A_SOUND = 343.0     # m/s
RED, BLUE, GREEN, PURPLE = "#c62828", "#1565c0", "#2e7d32", "#7b1fa2"


def size_prop(V_ms, thrust_N, rpm, slip, CT, rho, power_W=0.0):
    n = rpm / 60.0
    D = (thrust_N / (CT * rho * n ** 2)) ** 0.25
    V_pitch = V_ms / (1.0 - slip) if slip < 1.0 else float("inf")
    pitch = V_pitch / n
    tip = np.pi * D * n
    return {
        "n": n, "D": D, "pitch": pitch, "V_pitch": V_pitch,
        "PD": pitch / D, "J": V_ms / (n * D),
        "tip": tip, "mach": tip / A_SOUND,
        "eff": (thrust_N * V_ms / power_W) if power_W > 0 else None,
    }


# ============================================================
# Sidebar — design inputs
# ============================================================
st.title("🌀 Propeller — Diameter & Pitch Sizing")
st.caption("Size prop diameter and pitch from the wanted speed, available "
           "thrust per prop and motor RPM. ⚠️ Preliminary (static C_T) model.")

with st.sidebar:
    st.header("Design inputs")
    V_kmh = st.number_input("Wanted drone speed [km/h]", 1.0, 1000.0, 200.0,
                            5.0)
    thrust_N = st.number_input("Available thrust per prop [N]", 0.1, 500.0,
                               50.0, 1.0)
    rpm = st.number_input("Motor RPM", 500.0, 60000.0, 5000.0, 100.0,
                          help="≈ motor KV × battery voltage × ~0.8 (loaded)")
    slip = st.slider("Slip [-]", 0.05, 0.60, 0.25, 0.01,
                     help="Fraction the prop 'slips'; cruise V = "
                          "(1−slip)·pitch speed")
    st.subheader("Aero / motor")
    CT = st.number_input("Thrust coefficient C_T [-]", 0.01, 0.30, 0.10, 0.005,
                         format="%.3f")
    rho = st.number_input("Air density ρ [kg/m³]", 0.1, 2.0, 1.225, 0.001,
                          format="%.3f")
    n_motors = st.number_input("Number of motors", 1, 12, 4, 1)
    power_W = st.number_input("Electrical power per prop [W] (0 = skip)",
                              0.0, 20000.0, 0.0, 10.0)

V_ms = V_kmh / 3.6
r = size_prop(V_ms, thrust_N, rpm, slip, CT, rho, power_W)

# ---- Header metrics ----
st.subheader(f"Result:  **{r['D'] * M2IN:.1f} × {r['pitch'] * M2IN:.1f} in** "
             f"propeller  ({n_motors} motors)")
m = st.columns(4)
m[0].metric("Diameter D", f"{r['D'] * M2IN:.1f} in", f"{r['D'] * 100:.1f} cm")
m[1].metric("Pitch", f"{r['pitch'] * M2IN:.1f} in", f"{r['pitch'] * 100:.1f} cm")
m[2].metric("Pitch speed", f"{r['V_pitch']:.1f} m/s",
            f"{r['V_pitch'] * 3.6:.0f} km/h")
m[3].metric("Total thrust", f"{thrust_N * n_motors:.0f} N")
m2 = st.columns(4)
m2[0].metric("Pitch / Diameter", f"{r['PD']:.2f}")
m2[1].metric("Advance ratio J", f"{r['J']:.3f}")
m2[2].metric("Tip speed", f"{r['tip']:.0f} m/s", f"Mach {r['mach']:.2f}")
m2[3].metric("Prop efficiency",
             f"{r['eff'] * 100:.0f} %" if r['eff'] is not None else "—",
             help="T·V / P_elec (needs power input)")

if V_ms >= r["V_pitch"]:
    st.error("❌ Wanted speed ≥ pitch speed — impossible. Reduce speed, "
             "increase RPM, or lower slip.")
elif r["mach"] > 0.7:
    st.warning(f"⚠️ Tip Mach {r['mach']:.2f} > 0.7 — compressibility losses / "
               "noise. Use a smaller diameter or lower RPM.")
else:
    st.success(f"✅ Feasible: cruise at {V_kmh:.0f} km/h is "
               f"{(1 - slip) * 100:.0f}% of the pitch speed "
               f"({r['V_pitch'] * 3.6:.0f} km/h); tip Mach {r['mach']:.2f}.")

# ============================================================
# Tabs
# ============================================================
tab_thrust, tab_rpm, tab_about = st.tabs(
    ["📉 Thrust vs speed", "🔧 D & pitch vs RPM", "📖 Physics"])

# ---------- Dynamic thrust vs forward speed ----------
with tab_thrust:
    Vp = r["V_pitch"]
    v = np.linspace(0, Vp * 1.02, 200)
    T = thrust_N * np.clip(1 - v / Vp, 0, None)     # linear falloff to pitch spd
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=v, y=T, mode="lines",
                             line=dict(color=BLUE, width=3), name="thrust"))
    fig.add_vline(x=V_ms, line=dict(color=GREEN, dash="dash"),
                  annotation_text=f"wanted {V_kmh:.0f} km/h",
                  annotation_position="top left")
    fig.add_vline(x=Vp, line=dict(color=RED, dash="dot"),
                  annotation_text="pitch speed (T→0)",
                  annotation_position="top right")
    fig.add_hline(y=thrust_N, line=dict(color="grey", dash="dot"),
                  annotation_text=f"static {thrust_N:.0f} N",
                  annotation_position="bottom right")
    fig.update_layout(
        height=470, title="Approx. dynamic thrust vs forward speed",
        xaxis_title="Forward speed V [m/s]", yaxis_title="Thrust per prop [N]",
        yaxis=dict(rangemode="tozero"), margin=dict(t=60))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Simple linear model: thrust falls from its static value to "
               "zero at the pitch speed. The prop must be pitched so the "
               "wanted speed (green) stays left of the pitch speed (red).")

# ---------- D & pitch vs RPM ----------
with tab_rpm:
    rpm_arr = np.linspace(rpm * 0.4, rpm * 1.8, 200)
    D_arr, p_arr = [], []
    for rr in rpm_arr:
        s = size_prop(V_ms, thrust_N, rr, slip, CT, rho)
        D_arr.append(s["D"] * M2IN)
        p_arr.append(s["pitch"] * M2IN)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=rpm_arr, y=D_arr, mode="lines",
                             line=dict(color=BLUE, width=3), name="Diameter"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=rpm_arr, y=p_arr, mode="lines",
                             line=dict(color=PURPLE, width=3), name="Pitch"),
                  secondary_y=True)
    fig.add_vline(x=rpm, line=dict(color=GREEN, dash="dash"),
                  annotation_text=f"{rpm:.0f} RPM", annotation_position="top")
    fig.update_xaxes(title_text="Motor RPM")
    fig.update_yaxes(title_text="Diameter [in]", secondary_y=False,
                     color=BLUE)
    fig.update_yaxes(title_text="Pitch [in]", secondary_y=True, color=PURPLE)
    fig.update_layout(height=470, title="Diameter & pitch vs RPM "
                      "(fixed thrust & wanted speed)",
                      legend=dict(orientation="h", y=1.08),
                      margin=dict(t=70))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Higher RPM → smaller diameter (D ∝ RPM^−½) and smaller pitch "
               "(pitch ∝ RPM^−1) for the same thrust and wanted speed. Pick "
               "the RPM your motor/battery actually delivers.")

# ---------- Model ----------
with tab_about:
    st.markdown("### Sizing model")
    st.latex(r"D = \left(\frac{T}{C_T\,\rho\,n^2}\right)^{1/4}, \qquad n=\text{RPM}/60")
    st.latex(r"V_\text{pitch} = \frac{V}{1-\text{slip}}, \qquad "
             r"\text{pitch} = \frac{V_\text{pitch}}{n}")
    st.latex(r"J = \frac{V}{n\,D}, \qquad \frac{P}{D} = \frac{J}{1-\text{slip}},"
             r"\qquad V_\text{tip} = \pi D n")
    st.markdown(
        "- **Diameter** comes from the static thrust coefficient — it sets how "
        "much thrust the disc makes at the design RPM.\n"
        "- **Pitch** comes from the wanted speed and slip: the prop must "
        "advance `pitch` per rev fast enough that at `n` rev/s the no-slip "
        "speed exceeds the wanted speed by the slip margin.\n"
        "- Keep **tip Mach ≲ 0.7** and **P/D** in a sane range (≈0.3–0.8 for "
        "efficient props; >1 is a high-pitch 'speed' prop).")
    st.info("Preliminary model: static C_T (advance-ratio 0) and a linear "
            "thrust-vs-speed falloff. Replace C_T with prop-map / BEMT data "
            "for detailed design.")
