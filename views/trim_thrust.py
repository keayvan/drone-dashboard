# -*- coding: utf-8 -*-
"""
Drone Design Dashboard
======================
Interactive Streamlit front-end for the longitudinal trim & thrust
feasibility model (see steady_trimmed_flight_2DOF.py).
(Tail-sitter longitudinal trim analysis.)

Run:
    streamlit run drone_design_dashboard.py

Convention (tail-sitter / tilt-body):
    gamma = pitch angle from horizontal.
        90 deg -> hover  (fuselage & thrust vertical)
         0 deg -> full forward cruise
Trim (from Tx = Tz):   L = W*cos(gamma)
Trim speed:            v^2 = W*cos(gamma) / kL,     kL = 0.5*rho*CL0*S
Trim thrust:           T   = D + L*tan(gamma),      kD = 0.5*rho*CD0*A
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ============================================================
# Physics core (vectorised, pure — cached by Streamlit)
# ============================================================
G0 = 9.81


def coefficients(rho, S, A, CL0, CD0):
    """Return (kL, kD) so that L = kL*v^2 and D = kD*v^2."""
    kL = 0.5 * rho * CL0 * S
    kD = 0.5 * rho * CD0 * A
    return kL, kD


@st.cache_data(show_spinner=False)
def trim_curves(mass, rho, S, A, CL0, CD0, gamma_min, gamma_max, n=1000, g=G0):
    """
    Trim airspeed / thrust / lift / drag as functions of pitch angle gamma.

    Returns a DataFrame with columns:
        gamma_deg, v, T, L, D
    (rows where the trim solution is singular / non-physical are dropped).
    """
    W = mass * g
    kL, kD = coefficients(rho, S, A, CL0, CD0)

    gam = np.linspace(gamma_min, gamma_max, n)
    r = np.radians(gam)
    sg, cg = np.sin(r), np.cos(r)

    with np.errstate(divide="ignore", invalid="ignore"):
        v_sq = W * cg / kL
        v = np.sqrt(v_sq)
        L = kL * v_sq          # == W*cos(gamma)
        D = kD * v_sq
        T = D + L * np.tan(r)  # == (D*cos + L*sin)/cos

    ok = (cg > 1e-9) & (sg > 1e-9) & (v_sq > 0) & np.isfinite(T)
    return pd.DataFrame(
        {"gamma_deg": gam[ok], "v": v[ok], "T": T[ok], "L": L[ok], "D": D[ok]}
    )


@st.cache_data(show_spinner=False)
def feasibility_grid(mass, rho, S, A, CL0, CD0,
                     gamma_min, gamma_max, v_min, v_max,
                     n_gamma=220, n_v=220, g=G0):
    """
    Required-thrust and force-imbalance fields over the (v, gamma) plane.

    Returns (gammas_deg, vs, T_req, imbalance).
        T_req[i, j]     required thrust at gamma[i], v[j]  (max of the two axes)
        imbalance[i, j] |Tx - Tz|  (zero exactly on the trim curve)
    """
    W = mass * g
    kL, kD = coefficients(rho, S, A, CL0, CD0)

    gammas_deg = np.linspace(gamma_min, gamma_max, n_gamma)
    vs = np.linspace(v_min, v_max, n_v)
    Gr, V = np.meshgrid(np.radians(gammas_deg), vs, indexing="ij")
    sg, cg = np.sin(Gr), np.cos(Gr)

    L = kL * V**2
    D = kD * V**2
    Tx = (D * cg + L * sg) / cg
    Tz = (W + D * sg - L * cg) / sg

    imbalance = np.abs(Tx - Tz)
    T_req = np.maximum(Tx, Tz)
    return gammas_deg, vs, T_req, imbalance


def feasibility_crossings(df, T_available):
    """
    Points where the trim thrust curve crosses T_available.
    Returns list of (gamma, v, T) tuples (linearly interpolated).
    """
    g = df["gamma_deg"].to_numpy()
    v = df["v"].to_numpy()
    T = df["T"].to_numpy()
    diff = T - T_available
    idx = np.where(np.diff(np.sign(diff)) != 0)[0]
    out = []
    for i in idx:
        denom = diff[i] - diff[i + 1]
        if denom == 0:
            continue
        t = diff[i] / denom
        out.append((
            g[i] + t * (g[i + 1] - g[i]),
            v[i] + t * (v[i + 1] - v[i]),
            T_available,
        ))
    return out


# ============================================================
# Presets
# ============================================================
PRESETS = {
    "Baseline (placeholder aero)": dict(
        mass=5.0, rho=1.225, S=0.027, A=0.02, CL0=0.08, CD0=0.4, T_available=100.0
    ),
    "Cambered airfoil (NACA 2412-ish)": dict(
        mass=5.0, rho=1.225, S=0.10, A=0.02, CL0=0.20, CD0=0.05, T_available=100.0
    ),
    "Heavy lifter": dict(
        mass=12.0, rho=1.225, S=0.25, A=0.05, CL0=0.30, CD0=0.06, T_available=200.0
    ),
}

BLUE, RED, GREEN, PURPLE, ORANGE = (
    "#1565c0", "#c62828", "#2e7d32", "#7b1fa2", "#e65100"
)


# ============================================================
# Streamlit UI
# ============================================================
st.title("🚁 Trim & Thrust — Steady Flight Analysis")
st.caption("Longitudinal steady-trim & thrust feasibility (2-DOF). "
           "Pitch angle γ: 90° = hover, 0° = forward cruise.")

# ---- Sidebar: design parameters ----
with st.sidebar:
    st.header("Design parameters")

    preset_name = st.selectbox("Preset", list(PRESETS.keys()))
    p = PRESETS[preset_name]

    if st.button("↺ Reset to preset"):
        for k in ("mass", "rho", "S", "A", "CL0", "CD0", "T_available"):
            st.session_state[k] = p[k]

    st.subheader("Mass & environment")
    mass = st.number_input("Mass  m [kg]", 0.1, 100.0,
                           st.session_state.get("mass", p["mass"]), 0.1, key="mass")
    rho = st.number_input("Air density  ρ [kg/m³]", 0.1, 2.0,
                          st.session_state.get("rho", p["rho"]), 0.001,
                          format="%.3f", key="rho")

    st.subheader("Aerodynamics")
    S = st.number_input("Wing ref. area  S [m²]", 0.001, 5.0,
                        st.session_state.get("S", p["S"]), 0.001,
                        format="%.3f", key="S")
    A = st.number_input("Drag ref. area  A [m²]", 0.001, 5.0,
                        st.session_state.get("A", p["A"]), 0.001,
                        format="%.3f", key="A")
    CL0 = st.number_input("Lift coeff.  C_L0 [-]", 0.001, 2.5,
                          st.session_state.get("CL0", p["CL0"]), 0.01,
                          format="%.3f", key="CL0")
    CD0 = st.number_input("Drag coeff.  C_D0 [-]", 0.001, 2.5,
                          st.session_state.get("CD0", p["CD0"]), 0.01,
                          format="%.3f", key="CD0")

    st.subheader("Propulsion")
    T_available = st.number_input("Available thrust  T_avail [N]", 1.0, 1000.0,
                                  st.session_state.get("T_available", p["T_available"]),
                                  1.0, key="T_available")

    st.subheader("Analysis range")
    gamma_range = st.slider("Pitch angle γ [deg]", 1, 89, (5, 85))

# ---- Derived quantities / header metrics ----
W = mass * G0
kL, kD = coefficients(rho, S, A, CL0, CD0)
df = trim_curves(mass, rho, S, A, CL0, CD0, gamma_range[0], gamma_range[1])
crossings = feasibility_crossings(df, T_available)

T_min = float(df["T"].min())
T_max = float(df["T"].max())
v_top = float(df["v"].max())
feasible_frac = float((df["T"] <= T_available).mean()) * 100.0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Weight  W", f"{W:.1f} N")
m2.metric("Min trim thrust", f"{T_min:.1f} N")
m3.metric("Max trim thrust", f"{T_max:.1f} N")
m4.metric("Max trim speed", f"{v_top:.1f} m/s")
m5.metric("Feasible γ range", f"{feasible_frac:.0f} %",
          help="Fraction of the swept γ range where trim thrust ≤ T_avail")

if T_min > T_available:
    st.error(f"❌ Infeasible everywhere in this γ range — even the easiest "
             f"trim point needs {T_min:.1f} N > T_avail = {T_available:.0f} N.")
elif T_max <= T_available:
    st.success(f"✅ Fully feasible across γ = {gamma_range[0]}–{gamma_range[1]}° "
               f"(peak trim thrust {T_max:.1f} N ≤ {T_available:.0f} N).")
else:
    st.warning(f"⚠️ Partially feasible — trim thrust ranges "
               f"{T_min:.1f}–{T_max:.1f} N and crosses T_avail = "
               f"{T_available:.0f} N. See crossings below.")

# ============================================================
# Force-balance diagram (single V, gamma)
# ============================================================
def _bp(s, p, cg, sg):
    """Body-frame (s along nose, p perpendicular) -> world (x, z)."""
    return (s * cg - p * sg, s * sg + p * cg)


def _add_drone_glyph(fig, gr, r):
    """A simple bullet-shaped body at the origin, nose along the body axis."""
    cg, sg = np.cos(gr), np.sin(gr)
    body = "#1a1a1a"
    # bullet: ogive nose at +s, straight sides, flat base at -s
    pts = [(1.0, 0.0), (0.85, 0.10), (0.6, 0.17), (0.2, 0.20),
           (-0.9, 0.20), (-0.9, -0.20), (0.2, -0.20), (0.6, -0.17),
           (0.85, -0.10)]
    bx, bz = zip(*[_bp(s * r, p * r, cg, sg) for s, p in pts])
    fig.add_trace(go.Scatter(
        x=list(bx) + [bx[0]], y=list(bz) + [bz[0]], mode="lines",
        fill="toself", fillcolor=body, line=dict(color=body, width=1),
        opacity=0.9, showlegend=False, hoverinfo="skip"))


def _add_projections(fig, x, z, name, color):
    """Dashed component rectangle + Nx / Nz labels for a force vector."""
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


def force_diagram_figure(v, gamma_deg, mass, rho, S, A, CL0, CD0,
                         wingless=False, g=G0):
    """
    Trimmed force diagram for one (V, gamma), thrust free to tilt.

    The thrust vector is solved from BOTH balances (not fixed to the body
    axis):
        x-balance:  Tx = D*cos(g) + L*sin(g)
        z-balance:  Tz = W + D*sin(g) - L*cos(g)
        T = hypot(Tx, Tz),   thrust angle phi = atan2(Tz, Tx)
        tilt off flight path = phi - gamma
    With a wing and enough speed (L = W*cos g) the tilt is 0 (thrust along
    the body axis); with no wing the thrust must tilt up to carry the weight.
    Returns (fig, values).
    """
    W = mass * g
    kL, kD = coefficients(rho, S, A, CL0, CD0)
    gr = np.radians(gamma_deg)
    sg, cg = np.sin(gr), np.cos(gr)

    L = 0.0 if wingless else kL * v ** 2
    D = kD * v ** 2

    # thrust vector that trims BOTH axes (free to tilt off the flight path)
    Tx = D * cg + L * sg
    Tz = W + D * sg - L * cg
    T = float(np.hypot(Tx, Tz))
    phi = float(np.degrees(np.arctan2(Tz, Tx)))   # thrust angle from horizontal
    tilt = phi - gamma_deg                          # tilt off the flight path

    vectors = [
        ("T", Tx, Tz, RED),
        ("L", -L * sg, L * cg, BLUE),
        ("D", -D * cg, -D * sg, PURPLE),
        ("W", 0.0, -W, "black"),
    ]
    mag = max(T, L, D, W, 1e-6)
    R = mag * 1.35                  # symmetric square range, origin centred
    eps = 1e-6 * mag

    fig = go.Figure()
    # axes through origin
    fig.add_shape(type="line", x0=-R, x1=R, y0=0, y1=0,
                  line=dict(color="#2e7d32", width=1.5))
    fig.add_shape(type="line", x0=0, x1=0, y0=-R, y1=R,
                  line=dict(color="#2e7d32", width=1.5))
    # body axis / flight path (= velocity direction, alpha = 0)
    fig.add_shape(type="line", x0=-R * cg, x1=R * cg, y0=-R * sg, y1=R * sg,
                  line=dict(color="grey", width=1, dash="dot"))
    # drone glyph
    _add_drone_glyph(fig, gr, mag * 0.22)

    # gamma arc (horizontal -> flight path)
    rarc = mag * 0.22
    th = np.linspace(0, gr, 40)
    fig.add_trace(go.Scatter(x=rarc * np.cos(th), y=rarc * np.sin(th),
                             mode="lines", line=dict(color="black", width=1.4),
                             showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=rarc * 1.3 * np.cos(gr / 2),
                       y=rarc * 1.3 * np.sin(gr / 2),
                       text="γ", showarrow=False, font=dict(size=15))

    # tilt arc (flight path -> thrust direction) when thrust is not aligned
    if T > eps and abs(tilt) > 1.0:
        phir = np.radians(phi)
        rt = mag * 0.34
        tt = np.linspace(gr, phir, 40)
        fig.add_trace(go.Scatter(x=rt * np.cos(tt), y=rt * np.sin(tt),
                                 mode="lines",
                                 line=dict(color=RED, width=1.4, dash="dot"),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_annotation(x=rt * 1.18 * np.cos((gr + phir) / 2),
                           y=rt * 1.18 * np.sin((gr + phir) / 2),
                           text=f"{tilt:+.0f}°", showarrow=False,
                           font=dict(color=RED, size=12))

    # component guide lines (dashed, colour-matched) for T, L, D
    for name, x, z, color in vectors[:3]:
        if np.hypot(x, z) > eps:
            _add_projections(fig, x, z, name, color)

    # force vectors + labels (skip any that are ~zero, e.g. L when wingless)
    for name, x, z, color in vectors:
        if np.hypot(x, z) <= eps:
            continue
        fig.add_annotation(x=x, y=z, ax=0, ay=0, xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True,
                           arrowhead=3, arrowsize=1.2, arrowwidth=3.2,
                           arrowcolor=color)
        fig.add_annotation(x=x, y=z, text=f"<b>{name}</b>", showarrow=False,
                           font=dict(color=color, size=16),
                           xshift=16 if x >= 0 else -16,
                           yshift=16 if z >= 0 else -16)

    title = (f"Force diagram (α = 0, γ = {gamma_deg:.0f}°) — "
             f"thrust tilt {tilt:+.1f}° off flight path")
    fig.update_xaxes(range=[-R, R], title_text="Horizontal force component [N]",
                     zeroline=False, showgrid=False)
    fig.update_yaxes(range=[-R, R], title_text="Vertical force component [N]",
                     zeroline=False, showgrid=False,
                     scaleanchor="x", scaleratio=1)
    fig.update_layout(height=640, plot_bgcolor="white", showlegend=False,
                      title=title, margin=dict(t=60, l=40, r=40, b=40))

    return fig, dict(L=L, D=D, T=T, Tx=Tx, Tz=Tz, W=W, phi=phi, tilt=tilt)


# ============================================================
# Tabs
# ============================================================
tab_curves, tab_force, tab_map, tab_table, tab_about = st.tabs(
    ["📈 Trim curves", "⚖️ Force balance", "🗺️ Feasibility map",
     "📋 Data table", "📖 Physics"]
)

# ---------- Tab 1: trim curves ----------
with tab_curves:
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Trim airspeed vs pitch angle&nbsp;&nbsp;"
                        "(v² = W·cosγ / k_L)",
                        "Trim thrust vs pitch angle&nbsp;&nbsp;"
                        "(T = D + L·tanγ)"),
    )

    # Left: v(gamma)
    fig.add_trace(go.Scatter(
        x=df["gamma_deg"], y=df["v"], mode="lines", name="v_trim",
        line=dict(color=BLUE, width=3),
        hovertemplate="γ=%{x:.1f}°<br>v=%{y:.2f} m/s<extra></extra>"),
        row=1, col=1)

    # Right: T(gamma) + L, D + T_avail
    fig.add_trace(go.Scatter(
        x=df["gamma_deg"], y=df["T"], mode="lines", name="T_trim",
        line=dict(color=RED, width=3),
        hovertemplate="γ=%{x:.1f}°<br>T=%{y:.2f} N<extra></extra>"),
        row=1, col=2)
    fig.add_trace(go.Scatter(
        x=df["gamma_deg"], y=df["L"], mode="lines", name="Lift L",
        line=dict(color=BLUE, width=1.5, dash="dashdot")), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=df["gamma_deg"], y=df["D"], mode="lines", name="Drag D",
        line=dict(color=ORANGE, width=1.5, dash="dashdot")), row=1, col=2)

    # Reference lines — labels pinned to the LEFT edge so they never collide
    # with the crossing markers (which sit on the right side of the curve).
    fig.add_hline(y=W, line=dict(color="black", dash="dot"),
                  annotation_text=f"W = {W:.0f} N",
                  annotation_position="top left", row=1, col=2)
    fig.add_hline(y=T_available, line=dict(color=PURPLE, dash="dash", width=2),
                  annotation_text=f"T_avail = {T_available:.0f} N",
                  annotation_position="bottom left", row=1, col=2)

    # crossing markers — labels placed BELOW the marker, clear of the ref lines
    for (g_c, v_c, _) in crossings:
        fig.add_trace(go.Scatter(
            x=[g_c], y=[v_c], mode="markers+text", showlegend=False,
            marker=dict(color=RED, size=10),
            text=[f"γ={g_c:.1f}°"], textposition="bottom center",
            textfont=dict(color=RED)), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=[g_c], y=[T_available], mode="markers+text", showlegend=False,
            marker=dict(color=PURPLE, size=10),
            text=[f"γ={g_c:.1f}°, v={v_c:.1f} m/s"],
            textposition="bottom center",
            textfont=dict(color=PURPLE)), row=1, col=2)

    fig.update_xaxes(title_text="Pitch angle γ [deg]", row=1, col=1)
    fig.update_xaxes(title_text="Pitch angle γ [deg]", row=1, col=2)
    fig.update_yaxes(title_text="Trim airspeed v [m/s]", row=1, col=1)
    fig.update_yaxes(title_text="Thrust / Force [N]", row=1, col=2)
    fig.update_layout(height=520, hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.12,
                                  xanchor="right", x=1),
                      margin=dict(t=90))
    st.plotly_chart(fig, use_container_width=True)

    if crossings:
        st.markdown("**Feasibility boundary (T_trim = T_avail):**")
        st.dataframe(pd.DataFrame(
            [(f"{g:.2f}", f"{v:.2f}", f"{T:.1f}") for g, v, T in crossings],
            columns=["γ [deg]", "v_trim [m/s]", "T [N]"]),
            hide_index=True, use_container_width=False)

# ---------- Tab: force balance ----------
with tab_force:
    st.markdown(
        "Fully **trimmed** force balance for a chosen airspeed and pitch "
        "angle. Thrust is **free to tilt** off the flight path — it is solved "
        "from both axes: $T_x = D\\cos\\gamma + L\\sin\\gamma$ (horizontal) and "
        "$T_z = W + D\\sin\\gamma - L\\cos\\gamma$ (vertical), giving "
        "$T = \\sqrt{T_x^2 + T_z^2}$ and its direction. The **tilt off the "
        "flight path** shows how far thrust must point away from the velocity "
        "to carry the weight — zero with enough wing lift, large with no wing.")

    col_in, col_fig, col_out = st.columns([1, 2.6, 1.1], gap="large")

    # --- Left: inputs ---
    with col_in:
        st.subheader("Inputs")
        gamma_fb = st.slider("Pitch angle γ [deg]", 1, 89, 35, key="fb_gamma")
        kL_fb, _ = coefficients(rho, S, A, CL0, CD0)
        v_trim_here = float(np.sqrt(
            max(W * np.cos(np.radians(gamma_fb)) / kL_fb, 0.0)))
        v_max_slider = float(max(round(v_trim_here * 2), 10))
        v_fb = st.slider("Airspeed V [m/s]", 0.0, v_max_slider,
                         float(round(v_trim_here, 1)), key="fb_v",
                         help=f"With a wing, thrust tilt is 0 at "
                              f"≈ {v_trim_here:.1f} m/s (γ = {gamma_fb}°)")
        wingless = st.checkbox("Wingless (quad mode) — ignore lift",
                               value=False, key="fb_wingless",
                               help="Set L = 0. Thrust must tilt to carry the "
                                    "weight, like a normal quadcopter.")

    fig_fb, fb = force_diagram_figure(v_fb, gamma_fb, mass, rho, S, A, CL0, CD0,
                                      wingless=wingless)

    # --- Middle: figure ---
    with col_fig:
        st.plotly_chart(fig_fb, use_container_width=True)

    # --- Right: results ---
    with col_out:
        st.subheader("Results")
        st.metric("Lift L", f"{fb['L']:.1f} N")
        st.metric("Drag D", f"{fb['D']:.1f} N")
        st.metric("Tx (horiz.)", f"{fb['Tx']:.1f} N")
        st.metric("Tz (vert.)", f"{fb['Tz']:.1f} N")
        st.metric("T (total)", f"{fb['T']:.1f} N")
        st.metric("Thrust angle φ", f"{fb['phi']:.1f}°",
                  help="From horizontal")
        st.metric("Tilt off flight path", f"{fb['tilt']:+.1f}°")
        st.metric("Weight W", f"{fb['W']:.1f} N")

        if abs(fb["tilt"]) < 0.5:
            st.success("✅ Thrust aligned with the flight path — wing lift "
                       "carries the perpendicular weight.")
        else:
            st.info(f"↳ Thrust tilts **{fb['tilt']:+.1f}°** off the flight "
                    f"path to supply the perpendicular force the wing can't.")

# ---------- Tab 2: feasibility map ----------
with tab_map:
    c1, c2 = st.columns([3, 1])
    with c2:
        v_auto = round(v_top * 1.25, 1)
        v_hi = st.number_input("Max airspeed on map [m/s]", 1.0, 500.0,
                               float(max(v_auto, 5.0)), 1.0)
        field_choice = st.radio("Field", ["Required thrust", "Force imbalance"])
        cap = st.slider("Colour cap [N]", 10, 500, 150, 10)

    gammas_deg, vs, T_req, imbalance = feasibility_grid(
        mass, rho, S, A, CL0, CD0,
        gamma_range[0], gamma_range[1], 0.1, v_hi)

    if field_choice == "Required thrust":
        Z, cmap, label = np.clip(T_req, 0, cap), "Jet", "Required thrust [N]"
    else:
        Z, cmap, label = np.clip(imbalance, 0, cap), "Magma", "|Tx − Tz| [N]"

    cfig = go.Figure()
    cfig.add_trace(go.Contour(
        x=vs, y=gammas_deg, z=Z, colorscale=cmap,
        colorbar=dict(title=label),
        contours=dict(showlines=False),
        hovertemplate="v=%{x:.1f} m/s<br>γ=%{y:.1f}°<br>"
                      + label + "=%{z:.1f}<extra></extra>"))
    # trim curve overlay
    cfig.add_trace(go.Scatter(
        x=df["v"], y=df["gamma_deg"], mode="lines", name="Trim curve",
        line=dict(color="cyan", width=3)))
    # T_avail iso-line via a single contour level
    cfig.add_trace(go.Contour(
        x=vs, y=gammas_deg, z=T_req, showscale=False,
        contours=dict(start=T_available, end=T_available, size=1,
                      coloring="lines"),
        line=dict(color="white", width=2, dash="dash"),
        name=f"T_avail = {T_available:.0f} N", hoverinfo="skip"))

    cfig.update_layout(
        height=560, xaxis_title="Airspeed v [m/s]",
        yaxis_title="Pitch angle γ [deg]",
        title=f"{field_choice} over the (v, γ) plane "
              f"— white dashed = T_avail {T_available:.0f} N",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    with c1:
        st.plotly_chart(cfig, use_container_width=True)
    st.caption("The cyan **trim curve** is the equilibrium locus (imbalance = 0). "
               "The white dashed line is the feasibility boundary where required "
               "thrust equals the available thrust.")

# ---------- Tab 3: data table ----------
with tab_table:
    step = max(1, len(df) // 40)
    show = df.iloc[::step].copy()
    show["feasible"] = np.where(show["T"] <= T_available, "✅", "❌")
    show = show.rename(columns={
        "gamma_deg": "γ [deg]", "v": "v_trim [m/s]", "T": "T_trim [N]",
        "L": "L [N]", "D": "D [N]"})
    st.dataframe(show.style.format({
        "γ [deg]": "{:.1f}", "v_trim [m/s]": "{:.2f}", "T_trim [N]": "{:.2f}",
        "L [N]": "{:.2f}", "D [N]": "{:.2f}"}), hide_index=True,
        use_container_width=True, height=520)
    st.download_button(
        "⬇️ Download full trim sweep (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        file_name="trim_sweep.csv", mime="text/csv")

# ---------- Tab 4: physics ----------
with tab_about:
    st.markdown("### Model — 2-DOF longitudinal steady trim")
    st.markdown(
        r"Pitch angle $\gamma$ is measured from horizontal: "
        r"$\gamma = 90^\circ$ is hover (thrust vertical), "
        r"$\gamma \to 0^\circ$ is forward cruise. With $\alpha = 0$, "
        r"the velocity direction equals the body axis.")

    st.markdown("**Force balance**")
    st.latex(r"x:\quad T\cos\gamma - D\cos\gamma - L\sin\gamma = 0")
    st.latex(r"z:\quad T\sin\gamma + L\cos\gamma - W - D\sin\gamma = 0")

    st.markdown(r"**Closed-form trim** (eliminating $T$):")
    st.latex(r"L = W\cos\gamma \qquad "
             r"v^2 = \frac{W\cos\gamma}{k_L} \qquad "
             r"T = D + L\tan\gamma")
    st.markdown(
        r"with $k_L = \tfrac{1}{2}\rho\,C_{L0}\,S$ and "
        r"$k_D = \tfrac{1}{2}\rho\,C_{D0}\,A$.")

    st.info("Drag does **not** enter the trim-speed formula — lift and weight "
            "alone set the equilibrium speed; drag only sets the required thrust.")

    st.markdown(r"**Off-trim (contour) quantities** for any $(v, \gamma)$:")
    st.latex(r"T_x = \frac{D\cos\gamma + L\sin\gamma}{\cos\gamma} \qquad "
             r"T_z = \frac{W + D\sin\gamma - L\cos\gamma}{\sin\gamma} \qquad "
             r"T_\text{req} = \max(T_x,\, T_z)")
    st.markdown(r"The imbalance $|T_x - T_z|$ is zero exactly on the trim curve.")

    st.caption("Source model: `steady_trimmed_flight_2DOF.py`. "
            "The default preset uses ⚠️ placeholder aero coefficients "
            "(C_L0, C_D0) — replace them with values from your airfoil/CFD data.")
