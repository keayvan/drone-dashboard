# -*- coding: utf-8 -*-
"""
α-Trim — Self-Consistent Angle of Attack
========================================
Refinement of the Force-balance model. The rotors are fixed to the airframe,
so the drone points along the thrust; the angle between the body/thrust and
the flight path is the angle of attack α. The wing lift depends on α through
C_L(α) = C_L0 + C_Lα·α, so α and thrust must be solved together.

Wind-axis balance (∥ and ⊥ to velocity), body/thrust at angle α to the path:
    ∥:  T·cosα = D + W·sinγ
    ⊥:  T·sinα = W·cosγ − L(α)
  ⇒  tanα = (W·cosγ − L(α)) / (D + W·sinγ)      (solve for α)
     T     = (D + W·sinγ) / cosα
with  L(α) = q·S·(C_L0 + C_Lα·α),  D = q·A·(C_D0 + k·C_L²),  q = ½ρV².
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

G0 = 9.81
RED, BLUE, GREEN, PURPLE, ORANGE = (
    "#c62828", "#1565c0", "#2e7d32", "#7b1fa2", "#e65100")


# ============================================================
# Solver
# ============================================================
def solve_alpha(v, gamma_deg, mass, rho, S, A, CL0, CLa, CD0, k_ind=0.0,
                g=G0):
    """
    Self-consistent trim for one (V, gamma). Returns a dict of results.
    Solves tanα·(D + W·sinγ) = W·cosγ − L(α) for α by bisection.
    """
    W = mass * g
    gr = np.radians(gamma_deg)
    q = 0.5 * rho * v ** 2
    sg, cg = np.sin(gr), np.cos(gr)

    def forces(a):
        CL = CL0 + CLa * a
        L = q * S * CL
        CD = CD0 + k_ind * CL ** 2
        D = q * A * CD
        return CL, L, CD, D

    def resid(a):
        _, L, _, D = forces(a)
        return np.tan(a) * (D + W * sg) - (W * cg - L)

    lo, hi = np.radians(-85.0), np.radians(85.0)
    flo, fhi = resid(lo), resid(hi)
    if flo * fhi > 0:                      # no sign change — clamp to best end
        a = lo if abs(flo) < abs(fhi) else hi
    else:
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            fm = resid(mid)
            if flo * fm <= 0:
                hi = mid
            else:
                lo, flo = mid, fm
        a = 0.5 * (lo + hi)

    CL, L, CD, D = forces(a)
    T = (D + W * sg) / np.cos(a)
    return {
        "alpha": a, "alpha_deg": np.degrees(a),
        "phi_deg": gamma_deg + np.degrees(a),
        "T": float(T), "L": float(L), "D": float(D),
        "CL": float(CL), "CD": float(CD), "W": W,
    }


# ============================================================
# Force-diagram helpers (self-contained)
# ============================================================
def _bp(s, p, cg, sg):
    return (s * cg - p * sg, s * sg + p * cg)


def _drone(fig, ang, r):
    cg, sg = np.cos(ang), np.sin(ang)
    body = "#1a1a1a"
    pts = [(1.0, 0.0), (0.85, 0.10), (0.6, 0.17), (0.2, 0.20),
           (-0.9, 0.20), (-0.9, -0.20), (0.2, -0.20), (0.6, -0.17),
           (0.85, -0.10)]
    bx, bz = zip(*[_bp(s * r, p * r, cg, sg) for s, p in pts])
    fig.add_trace(go.Scatter(x=list(bx) + [bx[0]], y=list(bz) + [bz[0]],
                             mode="lines", fill="toself", fillcolor=body,
                             line=dict(color=body, width=1), opacity=0.9,
                             showlegend=False, hoverinfo="skip"))


def _proj(fig, x, z, name, color):
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=z,
                  line=dict(color=color, width=1, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=x, y0=z, y1=z,
                  line=dict(color=color, width=1, dash="dot"))
    fig.add_annotation(x=x / 2, y=z, text=f"{name}x", showarrow=False,
                       font=dict(color=color, size=11),
                       yshift=11 if z >= 0 else -11)
    fig.add_annotation(x=x, y=z / 2, text=f"{name}z", showarrow=False,
                       font=dict(color=color, size=11),
                       xshift=16 if x >= 0 else -16)


def aoa_force_figure(gamma_deg, sol):
    gr = np.radians(gamma_deg)
    sg, cg = np.sin(gr), np.cos(gr)
    a = sol["alpha"]
    phir = gr + a
    L, D, W, T = sol["L"], sol["D"], sol["W"], sol["T"]

    vectors = [
        ("T", T * np.cos(phir), T * np.sin(phir), RED),
        ("L", -L * sg, L * cg, BLUE),
        ("D", -D * cg, -D * sg, PURPLE),
        ("W", 0.0, -W, "black"),
    ]
    mag = max(T, L, D, W, 1e-6)
    R = mag * 1.35
    eps = 1e-6 * mag

    fig = go.Figure()
    fig.add_shape(type="line", x0=-R, x1=R, y0=0, y1=0,
                  line=dict(color=GREEN, width=1.5))
    fig.add_shape(type="line", x0=0, x1=0, y0=-R, y1=R,
                  line=dict(color=GREEN, width=1.5))
    # flight path (velocity) at gamma
    fig.add_shape(type="line", x0=-R * cg, x1=R * cg, y0=-R * sg, y1=R * sg,
                  line=dict(color="grey", width=1, dash="dot"))
    # body / thrust axis at phi
    fig.add_shape(type="line", x0=-R * np.cos(phir), x1=R * np.cos(phir),
                  y0=-R * np.sin(phir), y1=R * np.sin(phir),
                  line=dict(color=RED, width=1, dash="dot"))
    # drone points along body/thrust
    _drone(fig, phir, mag * 0.22)

    # gamma arc (horizontal -> flight path)
    rarc = mag * 0.20
    th = np.linspace(0, gr, 40)
    fig.add_trace(go.Scatter(x=rarc * np.cos(th), y=rarc * np.sin(th),
                             mode="lines", line=dict(color="black", width=1.4),
                             showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=rarc * 1.3 * np.cos(gr / 2),
                       y=rarc * 1.3 * np.sin(gr / 2), text="γ",
                       showarrow=False, font=dict(size=14))
    # alpha arc (flight path -> body/thrust)
    if abs(a) > np.radians(1):
        rt = mag * 0.33
        tt = np.linspace(gr, phir, 40)
        fig.add_trace(go.Scatter(x=rt * np.cos(tt), y=rt * np.sin(tt),
                                 mode="lines",
                                 line=dict(color=RED, width=1.4, dash="dot"),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_annotation(x=rt * 1.18 * np.cos((gr + phir) / 2),
                           y=rt * 1.18 * np.sin((gr + phir) / 2),
                           text=f"α={sol['alpha_deg']:+.0f}°", showarrow=False,
                           font=dict(color=RED, size=12))

    for name, x, z, color in vectors[:3]:
        if np.hypot(x, z) > eps:
            _proj(fig, x, z, name, color)
    for name, x, z, color in vectors:
        if np.hypot(x, z) <= eps:
            continue
        fig.add_annotation(x=x, y=z, ax=0, ay=0, xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True, arrowhead=3,
                           arrowsize=1.2, arrowwidth=3.2, arrowcolor=color)
        fig.add_annotation(x=x, y=z, text=f"<b>{name}</b>", showarrow=False,
                           font=dict(color=color, size=16),
                           xshift=16 if x >= 0 else -16,
                           yshift=16 if z >= 0 else -16)

    fig.update_xaxes(range=[-R, R], title_text="Horizontal force [N]",
                     zeroline=False, showgrid=False)
    fig.update_yaxes(range=[-R, R], title_text="Vertical force [N]",
                     zeroline=False, showgrid=False,
                     scaleanchor="x", scaleratio=1)
    fig.update_layout(
        height=640, plot_bgcolor="white", showlegend=False,
        title=f"Self-consistent trim — γ = {gamma_deg:.0f}°, "
              f"α = {sol['alpha_deg']:+.1f}°, φ = {sol['phi_deg']:.1f}°",
        margin=dict(t=60, l=40, r=40, b=40))
    return fig


# ============================================================
# Sidebar — vehicle / aero configuration
# ============================================================
st.title("📐 α-Trim — Self-Consistent Angle of Attack")
st.caption("Solves the true angle of attack α with lift-curve C_L(α) = "
           "C_L0 + C_Lα·α. The drone points along the thrust; α is the tilt "
           "of the body off the flight path. ⚠️ Placeholder aero.")

with st.sidebar:
    st.header("Vehicle & aero")
    mass = st.number_input("Mass m [kg]", 0.1, 100.0, 5.0, 0.1)
    rho = st.number_input("Air density ρ [kg/m³]", 0.1, 2.0, 1.225, 0.001,
                          format="%.3f")
    S = st.number_input("Wing area S [m²]", 0.001, 5.0, 0.10, 0.001,
                        format="%.3f")
    A = st.number_input("Drag ref area A [m²]", 0.001, 5.0, 0.02, 0.001,
                        format="%.3f")
    st.subheader("Lift curve  C_L(α) = C_L0 + C_Lα·α")
    CL0 = st.number_input("C_L0 [-]", -0.5, 2.0, 0.20, 0.01, format="%.3f")
    CLa = st.number_input("Lift slope C_Lα [1/rad]", 0.0, 10.0, 5.0, 0.1,
                          help="≈2π ideal; 4–6 for real wings")
    st.subheader("Drag  C_D = C_D0 + k·C_L²")
    CD0 = st.number_input("C_D0 [-]", 0.001, 2.5, 0.05, 0.005, format="%.3f")
    k_ind = st.number_input("Induced-drag k [-]", 0.0, 1.0, 0.05, 0.01,
                            format="%.3f", help="Set 0 for constant drag")
    stall_deg = st.number_input("Stall angle [deg]", 5.0, 30.0, 15.0, 1.0)

# reference speed where alpha = 0 (wing carries W·cosγ at C_L0), at gamma below
tab_diagram, tab_sweep = st.tabs(["⚖️ Force diagram", "📈 α & thrust vs speed"])

# ---------- Force diagram ----------
with tab_diagram:
    col_in, col_fig, col_out = st.columns([1, 2.6, 1.1], gap="large")
    with col_in:
        st.subheader("Inputs")
        gamma_d = st.slider("Flight-path angle γ [deg]", 1, 89, 20,
                            key="aoa_gamma")
        W = mass * G0
        q0 = 0.5 * rho * max(CL0, 1e-6) * S
        v0 = float(np.sqrt(max(W * np.cos(np.radians(gamma_d)) / q0, 0.0)))
        v_hi = float(max(round(v0 * 2), 10))
        v_d = st.slider("Airspeed V [m/s]", 1.0, v_hi,
                        float(round(max(v0, 1.0), 1)), key="aoa_v",
                        help=f"α = 0 at ≈ {v0:.1f} m/s for this γ")

    sol = solve_alpha(v_d, gamma_d, mass, rho, S, A, CL0, CLa, CD0, k_ind)

    with col_fig:
        st.plotly_chart(aoa_force_figure(gamma_d, sol),
                        use_container_width=True)

    with col_out:
        st.subheader("Results")
        st.metric("Angle of attack α", f"{sol['alpha_deg']:+.1f}°")
        st.metric("Thrust angle φ", f"{sol['phi_deg']:.1f}°",
                  help="From horizontal (= γ + α)")
        st.metric("Thrust T", f"{sol['T']:.1f} N")
        st.metric("Lift L", f"{sol['L']:.1f} N")
        st.metric("Drag D", f"{sol['D']:.1f} N")
        st.metric("C_L(α)", f"{sol['CL']:.3f}")
        st.metric("Weight W", f"{sol['W']:.1f} N")

        if abs(sol["alpha_deg"]) > stall_deg:
            st.error(f"⚠️ α = {sol['alpha_deg']:+.1f}° exceeds stall "
                     f"({stall_deg:.0f}°) — lift model no longer valid.")
        elif abs(sol["alpha_deg"]) < 0.5:
            st.success("✅ α ≈ 0 — wing alone carries the perpendicular "
                       "weight; thrust is along the flight path.")
        else:
            st.info(f"↳ Wing makes up part of the lift; thrust tilts so the "
                    f"body sits at α = {sol['alpha_deg']:+.1f}°.")

# ---------- Sweep ----------
with tab_sweep:
    gamma_s = st.slider("Flight-path angle γ [deg]", 1, 89, 20,
                        key="aoa_sweep_gamma")
    W = mass * G0
    q0 = 0.5 * rho * max(CL0, 1e-6) * S
    v0 = float(np.sqrt(max(W * np.cos(np.radians(gamma_s)) / q0, 0.0)))
    v_arr = np.linspace(3.0, max(v0 * 2.2, 20.0), 200)
    a_arr, T_arr = [], []
    for vv in v_arr:
        s = solve_alpha(vv, gamma_s, mass, rho, S, A, CL0, CLa, CD0, k_ind)
        a_arr.append(s["alpha_deg"])
        T_arr.append(s["T"])
    a_arr, T_arr = np.array(a_arr), np.array(T_arr)

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Angle of attack α vs airspeed",
                                        "Thrust T vs airspeed"))
    fig.add_trace(go.Scatter(x=v_arr, y=a_arr, mode="lines",
                             line=dict(color=RED, width=3), name="α"),
                  row=1, col=1)
    fig.add_hline(y=0, line=dict(color="grey", dash="dot"), row=1, col=1)
    fig.add_hline(y=stall_deg, line=dict(color=RED, dash="dash"),
                  annotation_text="stall", annotation_position="top left",
                  row=1, col=1)
    fig.add_hline(y=-stall_deg, line=dict(color=RED, dash="dash"),
                  row=1, col=1)
    if 3.0 <= v0 <= v_arr[-1]:
        fig.add_vline(x=v0, line=dict(color=GREEN, dash="dot"),
                      annotation_text=f"α=0 @ {v0:.0f} m/s",
                      annotation_position="top", row=1, col=1)
    fig.add_trace(go.Scatter(x=v_arr, y=T_arr, mode="lines",
                             line=dict(color=BLUE, width=3), name="T"),
                  row=1, col=2)
    fig.add_hline(y=W, line=dict(color="black", dash="dot"),
                  annotation_text=f"W = {W:.0f} N",
                  annotation_position="top left", row=1, col=2)
    fig.update_xaxes(title_text="Airspeed V [m/s]", row=1, col=1)
    fig.update_xaxes(title_text="Airspeed V [m/s]", row=1, col=2)
    fig.update_yaxes(title_text="α [deg]", row=1, col=1)
    fig.update_yaxes(title_text="Thrust T [N]", row=1, col=2)
    fig.update_layout(height=470, showlegend=False, margin=dict(t=60))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("At low speed the wing makes little lift, so the body pitches "
               "to a high α and the thrust tilts up to carry the weight. As "
               "speed rises, C_L(α) needs less α; α crosses 0 at the speed "
               "where the wing alone (at C_L0) balances W·cosγ, then goes "
               "slightly negative.")
