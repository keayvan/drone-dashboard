# -*- coding: utf-8 -*-
"""
Battery — Energy, Endurance & Sizing
====================================
Two directions:
  • Estimate flight time  — given a battery + operating point → time & range.
  • Size the battery      — given thrust per motor + target flight time →
                            required capacity and weight.

Energy:   E_pack = C_Ah·(S·V_cell);  E_usable = E_pack·DoD
Pack mass: m_batt = E_pack / e_specific
Hover power (momentum/actuator disk, per rotor):
          P = N · T^1.5 / (η·√(2ρ·A)),   A = πD²/4
Endurance = E_usable / P;   current I = P / V_nom  (must be ≤ C·C_Ah).
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

G0 = 9.81
RED, BLUE, GREEN, PURPLE, ORANGE = (
    "#c62828", "#1565c0", "#2e7d32", "#7b1fa2", "#e65100")


def hover_power_mass(m_total, rho, n_rotors, D, eta):
    W = m_total * G0
    A = n_rotors * np.pi * (D / 2) ** 2
    return W ** 1.5 / (eta * np.sqrt(2 * rho * A))


def hover_power_thrust(T_per, n_rotors, rho, D, eta):
    """Total hover power from thrust per rotor (momentum theory)."""
    A = np.pi * (D / 2) ** 2
    return n_rotors * T_per ** 1.5 / (eta * np.sqrt(2 * rho * A))


# ============================================================
# Sidebar
# ============================================================
st.title("🔋 Battery — Energy, Endurance & Sizing")
st.caption("Estimate flight time from a pack, or size the pack from thrust + "
           "target time. ⚠️ Preliminary momentum-theory model.")

with st.sidebar:
    goal = st.radio("Goal", ["Estimate flight time",
                             "Size battery (thrust + time)"])

    st.header("Cells & limits")
    S = st.number_input("Cells in series (S)", 1, 24, 6, 1)
    cellV = st.number_input("Nominal cell voltage [V]", 2.5, 4.2, 3.7, 0.05)
    dod = st.slider("Usable depth of discharge [%]", 50, 100, 80) / 100.0
    e_spec = st.number_input("Specific energy [Wh/kg]", 50.0, 400.0, 180.0, 5.0,
                             help="LiPo ≈ 150–200; Li-ion ≈ 200–260")
    Crate = st.number_input("Continuous C-rating", 1.0, 200.0, 30.0, 1.0)

    st.header("Propulsion")
    rho = st.number_input("Air density ρ [kg/m³]", 0.1, 2.0, 1.225, 0.001,
                          format="%.3f")
    eta = st.slider("Overall efficiency η", 0.20, 0.90, 0.55, 0.01,
                    help="Figure-of-merit × motor × ESC")
    P_avi = st.number_input("Avionics/payload power [W]", 0.0, 2000.0, 10.0, 1.0)

V_nom = S * cellV

# ============================================================
# MODE A — size the battery from thrust + target time
# ============================================================
if goal.startswith("Size"):
    with st.sidebar:
        st.header("Thrust & mission")
        n_mot = st.number_input("Number of motors", 1, 12, 4, 1)
        T_mot = st.number_input("Thrust per motor [N]", 0.1, 500.0, 12.0, 0.5)
        D = st.number_input("Rotor diameter [m]", 0.05, 3.0, 0.30, 0.01,
                            format="%.2f")
        t_s = st.number_input("Target flight time [s]", 1.0, 36000.0, 600.0,
                              10.0)
        dry = st.number_input("Dry mass w/o battery [kg] (0 = skip T/W)",
                              0.0, 100.0, 0.0, 0.1)

    T_total = n_mot * T_mot
    P = hover_power_thrust(T_mot, n_mot, rho, D, eta) + P_avi
    I_draw = P / V_nom

    E_use_need = P * (t_s / 3600.0)            # Wh usable required
    E_pack_energy = E_use_need / dod
    cap_energy_Ah = E_pack_energy / V_nom
    cap_current_Ah = I_draw / Crate            # so that C·cap ≥ I
    cap_Ah = max(cap_energy_Ah, cap_current_Ah)
    binding = "energy" if cap_energy_Ah >= cap_current_Ah else "current"
    E_pack = cap_Ah * V_nom
    m_batt = E_pack / e_spec

    st.subheader(f"Required pack:  **{cap_Ah * 1000:.0f} mAh**  ·  "
                 f"**{m_batt:.2f} kg**  ({S}S, {V_nom:.1f} V)")
    m = st.columns(4)
    m[0].metric("Required capacity", f"{cap_Ah * 1000:.0f} mAh",
                f"{binding}-limited")
    m[1].metric("Battery weight", f"{m_batt:.2f} kg",
                f"{m_batt * G0:.1f} N")
    m[2].metric("Pack energy", f"{E_pack:.0f} Wh", f"{V_nom:.1f} V")
    m[3].metric("Total thrust", f"{T_total:.0f} N")
    m2 = st.columns(4)
    m2[0].metric("Hover power", f"{P:.0f} W")
    m2[1].metric("Current draw", f"{I_draw:.0f} A")
    m2[2].metric("Flight time", f"{t_s:.0f} s", f"{t_s / 60:.1f} min")
    m2[3].metric("Energy / current cap",
                 f"{cap_energy_Ah * 1000:.0f} / {cap_current_Ah * 1000:.0f} mAh",
                 help="Capacity needed for energy vs for the C-rating current; "
                      "the larger one sizes the pack.")

    if binding == "current":
        st.warning(f"⚠️ Sized by **current**: {Crate:.0f}C can't supply "
                   f"{I_draw:.0f} A from the energy-only pack. Use a higher "
                   f"C-rating to shrink/lighten the battery.")
    else:
        st.success(f"✅ Sized by **energy**; {Crate:.0f}C easily covers the "
                   f"{I_draw:.0f} A draw.")

    if dry > 0:
        m_all = dry + m_batt
        tw = T_total / (m_all * G0)
        msg = (f"Total mass {m_all:.2f} kg → thrust-to-weight "
               f"**{tw:.2f}**.")
        if tw < 1.0:
            st.error("❌ " + msg + " Below 1 — can't even hover with this "
                     "battery. Reduce time, raise thrust, or lighter cells.")
        elif tw < 1.5:
            st.warning("⚠️ " + msg + " Marginal (<1.5) — little control margin.")
        else:
            st.info("✅ " + msg)

    tab_trade, tab_phys = st.tabs(["📈 Time trade", "📖 Physics"])
    with tab_trade:
        ts = np.linspace(max(t_s * 0.2, 30), t_s * 2.5, 200)
        cap_arr, wt_arr = [], []
        for tt in ts:
            ce = (P * tt / 3600.0 / dod) / V_nom
            ca = max(ce, cap_current_Ah)
            cap_arr.append(ca * 1000)
            wt_arr.append(ca * V_nom / e_spec)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=ts, y=cap_arr, mode="lines",
                                 line=dict(color=BLUE, width=3),
                                 name="Capacity"), secondary_y=False)
        fig.add_trace(go.Scatter(x=ts, y=wt_arr, mode="lines",
                                 line=dict(color=PURPLE, width=3),
                                 name="Weight"), secondary_y=True)
        fig.add_vline(x=t_s, line=dict(color=GREEN, dash="dash"),
                      annotation_text=f"target {t_s:.0f} s",
                      annotation_position="top left")
        fig.update_xaxes(title_text="Flight time [s]")
        fig.update_yaxes(title_text="Capacity [mAh]", secondary_y=False,
                         color=BLUE)
        fig.update_yaxes(title_text="Weight [kg]", secondary_y=True,
                         color=PURPLE)
        fig.update_layout(height=470, title="Required capacity & weight vs "
                          "target flight time", legend=dict(orientation="h",
                          y=1.08), margin=dict(t=70))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Both scale ~linearly with target time (until the C-rating "
                   "current floor takes over at short times).")

# ============================================================
# MODE B — estimate flight time from a given battery
# ============================================================
else:
    with st.sidebar:
        st.header("Battery pack")
        cap_mAh = st.number_input("Capacity [mAh]", 100.0, 100000.0, 5000.0,
                                  100.0)
        st.header("Operating point")
        mode = st.radio("Power model", ["Hover", "Cruise", "Given power"])
        if mode == "Hover":
            dry = st.number_input("Dry mass (no battery) [kg]", 0.1, 100.0,
                                  3.5, 0.1)
            n_rotors = st.number_input("Number of rotors", 1, 12, 4, 1)
            D = st.number_input("Rotor diameter [m]", 0.05, 3.0, 0.30, 0.01,
                                format="%.2f")
        elif mode == "Cruise":
            T_cruise = st.number_input("Cruise thrust / drag [N]", 0.1, 500.0,
                                       15.0, 0.5)
            V_kmh = st.number_input("Cruise speed [km/h]", 1.0, 500.0, 60.0,
                                    1.0)
        else:
            P_given = st.number_input("Average power [W]", 1.0, 50000.0, 600.0,
                                      10.0)
            V_kmh = st.number_input("Cruise speed for range [km/h] (0=none)",
                                    0.0, 500.0, 0.0, 1.0)

    cap_Ah = cap_mAh / 1000.0
    E_pack = cap_Ah * V_nom
    E_use = E_pack * dod
    m_batt = E_pack / e_spec
    I_max = Crate * cap_Ah

    if mode == "Hover":
        P = hover_power_mass(dry + m_batt, rho, n_rotors, D, eta) + P_avi
        V_ms = 0.0
    elif mode == "Cruise":
        V_ms = V_kmh / 3.6
        P = T_cruise * V_ms / eta + P_avi
    else:
        P = P_given + P_avi
        V_ms = V_kmh / 3.6

    I_draw = P / V_nom
    endurance_min = E_use / P * 60.0
    range_km = endurance_min / 60.0 * (V_ms * 3.6) if V_ms > 0 else 0.0

    m = st.columns(4)
    m[0].metric("Pack energy", f"{E_pack:.0f} Wh", f"{V_nom:.1f} V nominal")
    m[1].metric("Usable energy", f"{E_use:.0f} Wh", f"{dod*100:.0f}% DoD")
    m[2].metric("Pack mass", f"{m_batt:.2f} kg")
    m[3].metric("Max current (C·cap)", f"{I_max:.0f} A")
    m2 = st.columns(4)
    m2[0].metric("Power draw", f"{P:.0f} W")
    m2[1].metric("Current draw", f"{I_draw:.1f} A")
    m2[2].metric("Flight time", f"{endurance_min:.1f} min")
    m2[3].metric("Range", f"{range_km:.1f} km" if range_km > 0 else "—")

    if I_draw > I_max:
        st.error(f"❌ Current draw {I_draw:.0f} A exceeds pack limit "
                 f"{I_max:.0f} A (C·cap). Raise C-rating or capacity.")
    else:
        st.success(f"✅ Draw {I_draw:.0f} A is {I_draw/I_max*100:.0f}% of the "
                   f"{I_max:.0f} A pack limit — within rating.")

    tab_trade, tab_phys = st.tabs(["📈 Capacity trade study", "📖 Physics"])
    with tab_trade:
        caps = np.linspace(max(cap_mAh * 0.2, 500), cap_mAh * 3, 200)
        endur = []
        for c in caps:
            Eu = (c / 1000.0) * V_nom * dod
            mb = (c / 1000.0) * V_nom / e_spec
            if mode == "Hover":
                Pp = hover_power_mass(dry + mb, rho, n_rotors, D, eta) + P_avi
            elif mode == "Cruise":
                Pp = T_cruise * V_ms / eta + P_avi
            else:
                Pp = P_given + P_avi
            endur.append(Eu / Pp * 60.0)
        endur = np.array(endur)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=caps, y=endur, mode="lines",
                                 line=dict(color=BLUE, width=3)))
        fig.add_vline(x=cap_mAh, line=dict(color=GREEN, dash="dash"),
                      annotation_text=f"current {cap_mAh:.0f} mAh",
                      annotation_position="bottom right")
        if mode == "Hover":
            i = int(np.argmax(endur))
            fig.add_trace(go.Scatter(x=[caps[i]], y=[endur[i]],
                                     mode="markers+text", showlegend=False,
                                     marker=dict(color=RED, size=11),
                                     text=[f" max {endur[i]:.0f} min"],
                                     textposition="top center",
                                     textfont=dict(color=RED)))
        fig.update_layout(height=470, title="Flight time vs battery capacity",
                          xaxis_title="Capacity [mAh]",
                          yaxis_title="Flight time [min]",
                          yaxis=dict(rangemode="tozero"), margin=dict(t=60))
        st.plotly_chart(fig, use_container_width=True)
        if mode == "Hover":
            st.caption("In hover, flight time peaks at a battery mass ≈ 2× the "
                       "dry mass (power ∝ mass^1.5).")

# ============================================================
# Physics tab content (shared) — rendered into whichever tab_phys exists
# ============================================================
with tab_phys:
    st.markdown("### Battery, power & sizing model")
    st.latex(r"E_\text{pack} = C_{Ah}\,(S\cdot V_\text{cell}), \quad "
             r"E_\text{usable} = E_\text{pack}\cdot\text{DoD}, \quad "
             r"m_\text{batt} = E_\text{pack}/e_\text{spec}")
    st.markdown("**Hover power** (momentum theory, per rotor then summed):")
    st.latex(r"P = N\,\frac{T^{1.5}}{\eta\,\sqrt{2\rho A}}, \qquad "
             r"A = \tfrac{\pi D^2}{4}")
    st.markdown("**Estimate flight time** (given a pack):")
    st.latex(r"t = \frac{E_\text{usable}}{P}, \qquad I = \frac{P}{V_\text{nom}}"
             r"\le C_\text{rate} C_{Ah}")
    st.markdown("**Size the battery** (given thrust per motor and target "
                "time t): the pack must satisfy **both** energy and current —")
    st.latex(r"C_{Ah} = \max\!\left("
             r"\underbrace{\frac{P\,t/3600}{\text{DoD}\cdot V_\text{nom}}}"
             r"_{\text{energy}},\; "
             r"\underbrace{\frac{I}{C_\text{rate}}}_{\text{current}}\right), "
             r"\quad m_\text{batt} = \frac{C_{Ah} V_\text{nom}}{e_\text{spec}}")
    st.info("Feeds off Trim & Thrust (thrust) and Propeller (rotor diameter). "
            "η bundles figure-of-merit and drivetrain losses; replace with "
            "measured motor/pack data for detailed sizing.")
