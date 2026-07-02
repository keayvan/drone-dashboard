# -*- coding: utf-8 -*-
"""
Battery — Energy, Endurance & Range
===================================
Sizes flight time and range from the battery pack and the propulsion power.

Energy:     E_pack = (capacity_Ah)·(S·V_cell)   [Wh]
            E_usable = E_pack · DoD
Pack mass:  m_batt = E_pack / e_specific         [kg]
Power:
  Hover (momentum/actuator disk):
            P = W^1.5 / (η · √(2ρ·A_disk))       A_disk = N·πD²/4
  Cruise:   P = T·V / η
Endurance = E_usable / P;   Range = endurance · V_cruise.
Current draw I = P / V_nom must stay under C·capacity.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

G0 = 9.81
RED, BLUE, GREEN, PURPLE, ORANGE = (
    "#c62828", "#1565c0", "#2e7d32", "#7b1fa2", "#e65100")


def hover_power(m_total, rho, n_rotors, D, eta):
    W = m_total * G0
    A = n_rotors * np.pi * (D / 2) ** 2
    return W ** 1.5 / (eta * np.sqrt(2 * rho * A))


# ============================================================
# Sidebar
# ============================================================
st.title("🔋 Battery — Energy, Endurance & Range")
st.caption("Flight time and range from the pack energy and propulsion power. "
           "⚠️ Preliminary model (momentum-theory hover / simple cruise).")

with st.sidebar:
    st.header("Battery pack")
    cap_mAh = st.number_input("Capacity [mAh]", 100.0, 100000.0, 5000.0, 100.0)
    S = st.number_input("Cells in series (S)", 1, 24, 6, 1)
    cellV = st.number_input("Nominal cell voltage [V]", 2.5, 4.2, 3.7, 0.05)
    Crate = st.number_input("Continuous C-rating", 1.0, 200.0, 30.0, 1.0)
    dod = st.slider("Usable depth of discharge [%]", 50, 100, 80) / 100.0
    e_spec = st.number_input("Specific energy [Wh/kg]", 50.0, 400.0, 180.0, 5.0,
                             help="LiPo ≈ 150–200; Li-ion ≈ 200–260")

    st.subheader("Operating point")
    mode = st.radio("Power model", ["Hover", "Cruise", "Given power"])
    rho = st.number_input("Air density ρ [kg/m³]", 0.1, 2.0, 1.225, 0.001,
                          format="%.3f")
    P_avi = st.number_input("Avionics/payload power [W]", 0.0, 2000.0, 10.0, 1.0)
    eta = st.slider("Overall efficiency η", 0.20, 0.90, 0.55, 0.01,
                    help="Figure-of-merit × motor × ESC (hover) or "
                         "propulsive × drivetrain (cruise)")

    if mode == "Hover":
        dry = st.number_input("Dry mass (no battery) [kg]", 0.1, 100.0, 3.5,
                              0.1)
        n_rotors = st.number_input("Number of rotors", 1, 12, 4, 1)
        D = st.number_input("Rotor diameter [m]", 0.05, 3.0, 0.30, 0.01,
                            format="%.2f")
    elif mode == "Cruise":
        T_cruise = st.number_input("Cruise thrust / drag [N]", 0.1, 500.0,
                                   15.0, 0.5)
        V_kmh = st.number_input("Cruise speed [km/h]", 1.0, 500.0, 60.0, 1.0)
    else:
        P_given = st.number_input("Average power [W]", 1.0, 50000.0, 600.0,
                                  10.0)
        V_kmh = st.number_input("Cruise speed for range [km/h] (0 = none)",
                                0.0, 500.0, 0.0, 1.0)

# ---- Pack energy ----
V_nom = S * cellV
cap_Ah = cap_mAh / 1000.0
E_pack = cap_Ah * V_nom               # Wh
E_use = E_pack * dod
m_batt = E_pack / e_spec
I_max = Crate * cap_Ah

# ---- Power for the chosen mode ----
if mode == "Hover":
    m_total = dry + m_batt
    P_prop = hover_power(m_total, rho, n_rotors, D, eta)
    V_ms = 0.0
elif mode == "Cruise":
    P_prop = T_cruise * (V_kmh / 3.6) / eta
    V_ms = V_kmh / 3.6
else:
    P_prop = P_given
    V_ms = V_kmh / 3.6

P = P_prop + P_avi
I_draw = P / V_nom
endurance_min = E_use / P * 60.0
range_km = endurance_min / 60.0 * (V_ms * 3.6) if V_ms > 0 else 0.0

# ---- Header metrics ----
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
    st.error(f"❌ Current draw {I_draw:.0f} A exceeds the pack limit "
             f"{I_max:.0f} A (C·capacity). Raise C-rating or capacity.")
else:
    head = I_draw / I_max * 100
    st.success(f"✅ Draw {I_draw:.0f} A is {head:.0f}% of the {I_max:.0f} A "
               f"pack limit — within continuous rating.")

# ============================================================
# Tabs
# ============================================================
tab_trade, tab_phys = st.tabs(["📈 Capacity trade study", "📖 Physics"])

# ---------- Trade study ----------
with tab_trade:
    caps = np.linspace(max(cap_mAh * 0.2, 500), cap_mAh * 3, 200)
    endur, rng, mbatt_arr = [], [], []
    for c in caps:
        Ep = (c / 1000.0) * V_nom
        Eu = Ep * dod
        mb = Ep / e_spec
        if mode == "Hover":
            Pp = hover_power(dry + mb, rho, n_rotors, D, eta)
        elif mode == "Cruise":
            Pp = T_cruise * V_ms / eta
        else:
            Pp = P_given
        Pt = Pp + P_avi
        endur.append(Eu / Pt * 60.0)
        rng.append(Eu / Pt * (V_ms * 3.6) if V_ms > 0 else 0.0)
        mbatt_arr.append(mb)

    endur = np.array(endur)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=caps, y=endur, mode="lines",
                             line=dict(color=BLUE, width=3), name="flight time"))
    fig.add_vline(x=cap_mAh, line=dict(color=GREEN, dash="dash"),
                  annotation_text=f"current {cap_mAh:.0f} mAh",
                  annotation_position="bottom right")
    if mode == "Hover":
        # hover endurance peaks at m_batt = 2·dry  → find that capacity
        i_opt = int(np.argmax(endur))
        fig.add_trace(go.Scatter(x=[caps[i_opt]], y=[endur[i_opt]],
                                 mode="markers+text", showlegend=False,
                                 marker=dict(color=RED, size=11),
                                 text=[f" max {endur[i_opt]:.0f} min"],
                                 textposition="top center",
                                 textfont=dict(color=RED)))
    fig.update_layout(
        height=470, title="Flight time vs battery capacity",
        xaxis_title="Capacity [mAh]", yaxis_title="Flight time [min]",
        yaxis=dict(rangemode="tozero"), margin=dict(t=60))
    st.plotly_chart(fig, use_container_width=True)
    if mode == "Hover":
        st.caption("In hover, adding battery raises energy but also weight "
                   "(hover power ∝ mass^1.5), so flight time **peaks** at a "
                   "battery mass ≈ 2× the dry mass. Beyond that, extra cells "
                   "cost more than they add.")
    else:
        st.caption("With mass-independent cruise/given power, flight time is "
                   "proportional to capacity (a straight line).")

# ---------- Physics ----------
with tab_phys:
    st.markdown("### Battery & endurance model")
    st.latex(r"E_\text{pack} = C_{Ah}\,(S\cdot V_\text{cell}), \qquad "
             r"E_\text{usable} = E_\text{pack}\cdot \text{DoD}")
    st.latex(r"m_\text{batt} = E_\text{pack} / e_\text{specific}, \qquad "
             r"I_\text{max} = C_\text{rate}\cdot C_{Ah}")
    st.markdown("**Hover power** (momentum / actuator-disk theory):")
    st.latex(r"P_\text{hover} = \frac{W^{1.5}}{\eta\,\sqrt{2\rho A_\text{disk}}},"
             r"\qquad A_\text{disk} = N\,\tfrac{\pi D^2}{4}")
    st.markdown("**Cruise power:**")
    st.latex(r"P_\text{cruise} = \frac{T\,V}{\eta}")
    st.markdown("**Endurance, range, current:**")
    st.latex(r"t = \frac{E_\text{usable}}{P}, \qquad "
             r"R = t\,V_\text{cruise}, \qquad I = \frac{P}{V_\text{nom}}")
    st.markdown(
        "- $\\eta$ bundles the figure of merit and drivetrain losses "
        "(hover) or propulsive + drivetrain efficiency (cruise).\n"
        "- The **current draw must stay under $C_\\text{rate}\\cdot C_{Ah}$** "
        "or the pack sags / overheats.\n"
        "- Hover endurance has an optimum battery mass ≈ **2× the dry mass** "
        "(from $t \\propto m_\\text{batt}/(m_\\text{dry}+m_\\text{batt})^{1.5}$).")
    st.info("Feeds off the thrust (Trim & Thrust) and prop (Propeller) results. "
            "Replace η and specific energy with measured motor/pack data for "
            "detailed sizing.")
