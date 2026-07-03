# -*- coding: utf-8 -*-
"""
Battery — Energy, Endurance & Sizing
====================================
Tabs:
  • Size battery (thrust + time) → required capacity & weight
  • Estimate flight time (given a pack) → time & range
  • Time trade → capacity & weight vs target flight time
  • Physics

Energy:   E_pack = C_Ah·(S·V_cell);  E_usable = E_pack·DoD
Pack mass: m_batt = E_pack / e_specific
Hover power (momentum, per rotor): P = N·T^1.5 / (η·√(2ρ·A)),  A = πD²/4
Endurance = E_usable / P;   current I = P / V_nom  (≤ C·C_Ah).
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
    A = np.pi * (D / 2) ** 2
    return n_rotors * T_per ** 1.5 / (eta * np.sqrt(2 * rho * A))


def battery_settings(p):
    """Shared cell/propulsion inputs in an expander. `p` = key prefix."""
    with st.expander("⚙️ Battery & propulsion settings", expanded=False):
        S = st.number_input("Cells in series (S)", 1, 24, 6, 1, key=p + "S")
        cellV = st.number_input("Nominal cell voltage [V]", 2.5, 4.2, 3.7,
                                0.05, key=p + "cv")
        dod = st.slider("Usable depth of discharge [%]", 50, 100, 80,
                        key=p + "dod") / 100.0
        e_spec = st.number_input("Specific energy [Wh/kg]", 50.0, 400.0, 180.0,
                                 5.0, key=p + "es")
        Crate = st.number_input("Continuous C-rating", 1.0, 200.0, 30.0, 1.0,
                                key=p + "cr")
        rho = st.number_input("Air density ρ [kg/m³]", 0.1, 2.0, 1.225, 0.001,
                              format="%.3f", key=p + "rho")
        eta = st.slider("Overall efficiency η", 0.20, 0.90, 0.55, 0.01,
                        key=p + "eta")
        P_avi = st.number_input("Avionics/payload power [W]", 0.0, 2000.0, 10.0,
                                1.0, key=p + "avi")
    return dict(S=S, cellV=cellV, dod=dod, e_spec=e_spec, Crate=Crate,
                rho=rho, eta=eta, P_avi=P_avi, V_nom=S * cellV)


# ============================================================
st.title("🔋 Battery — Energy, Endurance & Sizing")
st.caption("Size a pack from thrust + target time, or estimate flight time "
           "from a pack. ⚠️ Preliminary momentum-theory model.")

tab_size, tab_est, tab_trade, tab_phys = st.tabs(
    ["🔧 Size battery", "⏱️ Estimate flight time", "📈 Time trade",
     "📖 Physics"])

# ============================================================
# TAB 1 — Size the battery from thrust + target time
# ============================================================
with tab_size:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("Inputs")
        n_mot = st.number_input("Number of motors", 1, 12, 4, 1, key="sz_n")
        T_mot = st.number_input("Thrust per motor [N]", 0.1, 500.0, 12.0, 0.5,
                                key="sz_T")
        D = st.number_input("Rotor diameter [m]", 0.05, 3.0, 0.30, 0.01,
                            format="%.2f", key="sz_D")
        t_s = st.number_input("Target flight time [s]", 1.0, 36000.0, 600.0,
                              10.0, key="sz_t")
        dry = st.number_input("Dry mass w/o battery [kg] (0 = skip T/W)",
                              0.0, 100.0, 0.0, 0.1, key="sz_dry")
        cfg = battery_settings("sz_")

    V_nom = cfg["V_nom"]
    T_total = n_mot * T_mot
    P = hover_power_thrust(T_mot, n_mot, cfg["rho"], D, cfg["eta"]) + cfg["P_avi"]
    I_draw = P / V_nom
    E_use_need = P * (t_s / 3600.0)
    E_pack_energy = E_use_need / cfg["dod"]
    cap_energy_Ah = E_pack_energy / V_nom
    cap_current_Ah = I_draw / cfg["Crate"]
    cap_Ah = max(cap_energy_Ah, cap_current_Ah)
    binding = "energy" if cap_energy_Ah >= cap_current_Ah else "current"
    E_pack = cap_Ah * V_nom
    m_batt = E_pack / cfg["e_spec"]

    # stash for the Time-trade tab
    _trade = dict(P=P, V_nom=V_nom, dod=cfg["dod"], e_spec=cfg["e_spec"],
                  cap_current_Ah=cap_current_Ah, t_s=t_s)

    with col_out:
        st.subheader("Results")
        st.metric("Required capacity", f"{cap_Ah * 1000:.0f} mAh",
                  f"{binding}-limited")
        st.metric("Battery weight", f"{m_batt:.2f} kg", f"{m_batt * G0:.1f} N")
        a, b = st.columns(2)
        a.metric("Pack energy", f"{E_pack:.0f} Wh")
        b.metric("Nominal voltage", f"{V_nom:.1f} V")
        a.metric("Hover power", f"{P:.0f} W")
        b.metric("Current draw", f"{I_draw:.0f} A")
        a.metric("Total thrust", f"{T_total:.0f} N")
        b.metric("Energy/current cap",
                 f"{cap_energy_Ah*1000:.0f}/{cap_current_Ah*1000:.0f}",
                 help="mAh needed for energy vs for the C-rating current; "
                      "the larger sizes the pack.")

        if binding == "current":
            st.warning(f"⚠️ **Current-limited**: {cfg['Crate']:.0f}C can't "
                       f"supply {I_draw:.0f} A from the energy-only pack — a "
                       f"higher C-rating shrinks/lightens the battery.")
        else:
            st.success(f"✅ **Energy-limited**; {cfg['Crate']:.0f}C easily "
                       f"covers the {I_draw:.0f} A draw.")

        if dry > 0:
            m_all = dry + m_batt
            tw = T_total / (m_all * G0)
            if tw < 1.0:
                st.error(f"❌ Total {m_all:.2f} kg → T/W **{tw:.2f}** (<1): "
                         f"can't hover with this battery.")
            elif tw < 1.5:
                st.warning(f"⚠️ Total {m_all:.2f} kg → T/W **{tw:.2f}** "
                           f"(<1.5): marginal control margin.")
            else:
                st.info(f"✅ Total {m_all:.2f} kg → T/W **{tw:.2f}**.")

# ============================================================
# TAB 2 — Estimate flight time from a given battery
# ============================================================
with tab_est:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("Inputs")
        cap_mAh = st.number_input("Capacity [mAh]", 100.0, 100000.0, 5000.0,
                                  100.0, key="es_cap")
        mode = st.radio("Power model", ["Hover", "Cruise", "Given power"],
                        horizontal=True, key="es_mode")
        if mode == "Hover":
            e_dry = st.number_input("Dry mass (no battery) [kg]", 0.1, 100.0,
                                    3.5, 0.1, key="es_dry")
            e_n = st.number_input("Number of rotors", 1, 12, 4, 1, key="es_n")
            e_D = st.number_input("Rotor diameter [m]", 0.05, 3.0, 0.30, 0.01,
                                  format="%.2f", key="es_D")
        elif mode == "Cruise":
            e_T = st.number_input("Cruise thrust / drag [N]", 0.1, 500.0, 15.0,
                                  0.5, key="es_Tc")
            e_V = st.number_input("Cruise speed [km/h]", 1.0, 500.0, 60.0, 1.0,
                                  key="es_Vc")
        else:
            e_P = st.number_input("Average power [W]", 1.0, 50000.0, 600.0,
                                  10.0, key="es_P")
            e_V = st.number_input("Cruise speed for range [km/h] (0=none)",
                                  0.0, 500.0, 0.0, 1.0, key="es_Vg")
        cfg2 = battery_settings("es_")

    V_nom2 = cfg2["V_nom"]
    cap_Ah2 = cap_mAh / 1000.0
    E_pack2 = cap_Ah2 * V_nom2
    E_use2 = E_pack2 * cfg2["dod"]
    m_batt2 = E_pack2 / cfg2["e_spec"]
    I_max2 = cfg2["Crate"] * cap_Ah2

    if mode == "Hover":
        P2 = hover_power_mass(e_dry + m_batt2, cfg2["rho"], e_n, e_D,
                              cfg2["eta"]) + cfg2["P_avi"]
        V_ms2 = 0.0
    elif mode == "Cruise":
        V_ms2 = e_V / 3.6
        P2 = e_T * V_ms2 / cfg2["eta"] + cfg2["P_avi"]
    else:
        P2 = e_P + cfg2["P_avi"]
        V_ms2 = e_V / 3.6

    I_draw2 = P2 / V_nom2
    endurance_min = E_use2 / P2 * 60.0
    range_km = endurance_min / 60.0 * (V_ms2 * 3.6) if V_ms2 > 0 else 0.0

    with col_out:
        st.subheader("Results")
        a, b = st.columns(2)
        a.metric("Flight time", f"{endurance_min:.1f} min")
        b.metric("Range", f"{range_km:.1f} km" if range_km > 0 else "—")
        a.metric("Pack energy", f"{E_pack2:.0f} Wh")
        b.metric("Usable energy", f"{E_use2:.0f} Wh")
        a.metric("Power draw", f"{P2:.0f} W")
        b.metric("Current draw", f"{I_draw2:.1f} A")
        a.metric("Pack mass", f"{m_batt2:.2f} kg")
        b.metric("Max current (C·cap)", f"{I_max2:.0f} A")

        if I_draw2 > I_max2:
            st.error(f"❌ Draw {I_draw2:.0f} A exceeds pack limit "
                     f"{I_max2:.0f} A — raise C-rating or capacity.")
        else:
            st.success(f"✅ Draw {I_draw2:.0f} A is {I_draw2/I_max2*100:.0f}% "
                       f"of the {I_max2:.0f} A pack limit.")

# ============================================================
# TAB 3 — Time trade (uses the Size-battery inputs)
# ============================================================
with tab_trade:
    st.caption("Required capacity & weight vs target flight time — driven by "
               "the inputs on the **Size battery** tab.")
    P = _trade["P"]; V_nom = _trade["V_nom"]; dod = _trade["dod"]
    e_spec = _trade["e_spec"]; cap_current_Ah = _trade["cap_current_Ah"]
    t_s = _trade["t_s"]

    ts = np.linspace(max(t_s * 0.2, 30), t_s * 2.5, 200)
    cap_arr, wt_arr = [], []
    for tt in ts:
        ce = (P * tt / 3600.0 / dod) / V_nom
        ca = max(ce, cap_current_Ah)
        cap_arr.append(ca * 1000)
        wt_arr.append(ca * V_nom / e_spec)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=ts, y=cap_arr, mode="lines",
                             line=dict(color=BLUE, width=3), name="Capacity"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=ts, y=wt_arr, mode="lines",
                             line=dict(color=PURPLE, width=3), name="Weight"),
                  secondary_y=True)
    fig.add_vline(x=t_s, line=dict(color=GREEN, dash="dash"),
                  annotation_text=f"target {t_s:.0f} s",
                  annotation_position="top left")
    fig.update_xaxes(title_text="Flight time [s]")
    fig.update_yaxes(title_text="Capacity [mAh]", secondary_y=False, color=BLUE)
    fig.update_yaxes(title_text="Weight [kg]", secondary_y=True, color=PURPLE)
    fig.update_layout(height=470, title="Required capacity & weight vs target "
                      "flight time", legend=dict(orientation="h", y=1.08),
                      margin=dict(t=70))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Both scale ~linearly with target time (until the C-rating "
               "current floor takes over at short times).")

# ============================================================
# TAB 4 — Physics
# ============================================================
with tab_phys:
    st.markdown(
        "Both modes are the same physics chain — **thrust → power → energy → "
        "capacity → weight** — run in opposite directions.")
    st.markdown(
        "We used:")
        st.markdown(
        "We used")

    # ---------- Size battery ----------
    st.subheader("🔧 Size battery — from thrust + target time")

    st.markdown("**1 · Thrust → power** (momentum / actuator-disk theory). "
                "Each rotor holds itself up by flinging air down; the power "
                "grows as $T^{1.5}$ and shrinks with disc area $A$:")
    st.latex(r"P = N\,\frac{T^{1.5}}{\eta\,\sqrt{2\rho A}} + P_\text{avionics},"
             r"\qquad A = \tfrac{\pi D^2}{4}")

    st.markdown("**2 · Power → energy** — sustain that power for the target "
                "time $t$ (seconds):")
    st.latex(r"E_\text{needed} = P \cdot \tfrac{t}{3600}\quad[\text{Wh}]")

    st.markdown(r"**3 · Energy → capacity** — a pack stores "
                r"$E = C_{Ah}\,V_\text{nom}$ with $V_\text{nom}=S\,V_\text{cell}$, "
                r"and only a fraction (DoD) is usable, so it must hold *more*:")
    st.latex(r"C_{Ah}^{\text{energy}} = "
             r"\frac{E_\text{needed}}{\text{DoD}\cdot V_\text{nom}}")

    st.markdown(r"**4 · Current check** — the pack must also *deliver* the "
                r"draw $I = P/V_\text{nom}$ within its C-rating. Whichever "
                r"limit is harder sizes the pack:")
    st.latex(r"C_{Ah} = \max\!\Big(\,C_{Ah}^{\text{energy}},\; "
             r"\tfrac{I}{C_\text{rate}}\,\Big)")

    st.markdown("**5 · Capacity → weight** — from the cells' specific energy "
                "(Wh/kg):")
    st.latex(r"m_\text{batt} = \frac{C_{Ah}\,V_\text{nom}}{e_\text{spec}}")
    st.caption("Long, gentle flights come out **energy-limited**; short "
               "high-power ones come out **current-limited** — the results "
               "panel flags which one binds.")

    st.divider()

    # ---------- Estimate flight time ----------
    st.subheader("⏱️ Estimate flight time — from a given pack")

    st.markdown("**1 · Usable energy** stored in the pack:")
    st.latex(r"E_\text{usable} = C_{Ah}\,(S\,V_\text{cell})\cdot\text{DoD}")

    st.markdown("**2 · Power draw** for the chosen operating point:")
    st.latex(r"P_\text{hover} = N\,\frac{T^{1.5}}{\eta\sqrt{2\rho A}}, \qquad "
             r"P_\text{cruise} = \frac{T\,V}{\eta} \qquad (+\,P_\text{avionics})")

    st.markdown("**3 · Flight time** = energy ÷ power; **range** = time × "
                "cruise speed:")
    st.latex(r"t = \frac{E_\text{usable}}{P}, \qquad R = t\,V")

    st.markdown("**4 · Feasibility** — the current must stay under the "
                "C-rating limit or the pack sags / overheats:")
    st.latex(r"I = \frac{P}{V_\text{nom}} \;\le\; C_\text{rate}\,C_{Ah}")

    st.divider()
    st.info("⚠️ Momentum-theory / hover model with a lumped efficiency η "
            "(rotor figure-of-merit × motor × ESC), constant power over the "
            "flight, and no thrust-to-weight feedback (use the optional "
            "dry-mass input for the T/W check). Swap η and specific energy for "
            "measured motor/pack data for detailed sizing.")
