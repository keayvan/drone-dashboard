# -*- coding: utf-8 -*-
"""
Weight & Cost — Component Bill of Materials
===========================================
Add up every component of the vehicle across three groups and get:
  • total weight (with and without the battery)
  • total price
  • a bill of materials (BOM) table

Groups:
  Propulsion      → Motor(s), ESC(s), Battery
  Avionic system  → Flight controller (FC), Sensor(s)
  Airframe        → Parts 1..n

All weights are in grams (gr); all prices in euro (€).
"""

import pandas as pd
import streamlit as st

st.title("⚖️ Weight & Cost — Bill of Materials")
st.caption(
    "Enter each component's unit weight and price. The dashboard sums them into "
    "total weight (with and without the battery), total cost and a full BOM.")

# Give each bordered section box a slightly lighter fill so groups separate
# clearly against the black background.
st.markdown(
    """
    <style>
    /* every section box carries a key starting with "wbox" */
    [class*="st-key-wbox"] {
        background: #2b2f37 !important;
        border: 1px solid #3c414a !important;
        border-radius: 12px !important;
        padding: 0.75rem 0.9rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True)

# Results render at the TOP but are computed from the inputs below — reserve
# the space here and fill it once everything is calculated.
results_area = st.container()

st.subheader("Inputs")
prop_col, avi_col, frame_col, gs_col = st.columns(4)

# --------------------------------------------------------------------------
# PROPULSION
# --------------------------------------------------------------------------
with prop_col:
    st.markdown("### 🌀 Propulsion")

    with st.container(border=True, key="wbox_mot"):
        st.markdown("**Motor(s)**")
        mot_name = st.text_input("Name", "Motor", key="mot_name")
        n_mot = st.number_input("Number of motors", 0, 64, 4, 1, key="n_mot")
        mot_w = st.number_input("Unit weight [gr]", 0.0, 1e5, 60.0, 1.0,
                                key="mot_w")
        mot_p = st.number_input("Unit price [€]", 0.0, 1e6, 25.0, 1.0,
                                key="mot_p")

    with st.container(border=True, key="wbox_esc"):
        st.markdown("**ESC(s)**")
        esc_name = st.text_input("Name", "ESC", key="esc_name")
        n_esc = st.number_input("Number of ESCs", 0, 64, 4, 1, key="n_esc")
        esc_w = st.number_input("Unit weight [gr]", 0.0, 1e5, 12.0, 1.0,
                                key="esc_w")
        esc_p = st.number_input("Unit price [€]", 0.0, 1e6, 15.0, 1.0,
                                key="esc_p")

    with st.container(border=True, key="wbox_bat"):
        st.markdown("**Battery**")
        bat_name = st.text_input("Name", "LiPo pack", key="bat_name")
        bat_w = st.number_input("Weight [gr]", 0.0, 1e5, 400.0, 1.0,
                                key="bat_w")
        bat_p = st.number_input("Price [€]", 0.0, 1e6, 60.0, 1.0, key="bat_p")

# --------------------------------------------------------------------------
# AVIONIC SYSTEM
# --------------------------------------------------------------------------
with avi_col:
    st.markdown("### 🧠 Avionic system")

    with st.container(border=True, key="wbox_fc"):
        st.markdown("**Flight controller (FC)**")
        fc_name = st.text_input("Name", "Flight controller", key="fc_name")
        fc_w = st.number_input("Weight [gr]", 0.0, 1e5, 60.0, 1.0, key="fc_w")
        fc_p = st.number_input("Price [€]", 0.0, 1e6, 200.0, 1.0, key="fc_p")

    with st.container(border=True, key="wbox_sensors"):
        st.markdown("**Sensor(s)**")
        st.caption("Add one row per sensor (GPS, IMU, camera, lidar…).")
        sensors = st.data_editor(
            pd.DataFrame([
                {"Name": "Power Distribution board", "Weight [gr]": 50.5, "Price [€]": 40.0},
                {"Name": "Current & voltage", "Weight [gr]": 30.0, "Price [€]": 10.0},
                {"Name": "GPS", "Weight [gr]": 10.0, "Price [€]": 30.0},
                {"Name": "Camera", "Weight [gr]": 25.0, "Price [€]": 90.0},
            ]),
            num_rows="dynamic", hide_index=True, use_container_width=True,
            key="sensors")

    with st.container(border=True, key="wbox_comm"):
        st.markdown("**Communication — air unit**")
        st.caption("On-board radio link (VTX, air unit, antenna, receiver…).")
        comm_air = st.data_editor(
            pd.DataFrame([
                {"Name": "Air unit / VTX", "Weight [gr]": 30.0,
                 "Price [€]": 130.0},
                {"Name": "Antenna", "Weight [gr]": 8.0, "Price [€]": 20.0},
            ]),
            num_rows="dynamic", hide_index=True, use_container_width=True,
            key="comm_air")

# --------------------------------------------------------------------------
# AIRFRAME
# --------------------------------------------------------------------------
with frame_col:
    st.markdown("### 🛩️ Airframe")

    with st.container(border=True, key="wbox_frame"):
        st.markdown("**Parts**")
        st.caption("Add one row per structural part (frame, arms, canopy…).")
        frame = st.data_editor(
            pd.DataFrame([
                {"Name": "Frame", "Weight [gr]": 180.0, "Price [€]": 70.0},
                {"Name": "Arms", "Weight [gr]": 60.0, "Price [€]": 20.0},
            ]),
            num_rows="dynamic", hide_index=True, use_container_width=True,
            key="frame")

# --------------------------------------------------------------------------
# GROUND STATION  (stays on the ground → excluded from flight weight)
# --------------------------------------------------------------------------
with gs_col:
    st.markdown("### 📡 Ground station")

    with st.container(border=True, key="wbox_ground"):
        st.markdown("**Components**")
        st.caption("Transmitter, goggles, monitor, antenna… Counted in cost, "
                   "but **not** in the vehicle flight weight.")
        ground = st.data_editor(
            pd.DataFrame([
                {"Name": "Transmitter", "Weight [gr]": 500.0,
                 "Price [€]": 200.0},
                {"Name": "Goggles", "Weight [gr]": 600.0, "Price [€]": 350.0},
            ]),
            num_rows="dynamic", hide_index=True, use_container_width=True,
            key="ground")


# --------------------------------------------------------------------------
# BILL OF MATERIALS
# --------------------------------------------------------------------------
def _rows_from_editor(df, group, offvehicle=False):
    """Turn a data_editor frame into BOM rows (skips blank/NaN rows)."""
    rows = []
    for _, r in df.iterrows():
        name = str(r.get("Name", "") or "").strip()
        w = float(r.get("Weight [gr]", 0) or 0)
        p = float(r.get("Price [€]", 0) or 0)
        if not name and w == 0 and p == 0:
            continue
        rows.append({"Group": group, "Component": name or "—", "Number": 1,
                     "Weight [gr]": w, "Price [€]": p, "_offvehicle": offvehicle})
    return rows


bom = [
    {"Group": "Propulsion", "Component": mot_name, "Number": int(n_mot),
     "Weight [gr]": n_mot * mot_w, "Price [€]": n_mot * mot_p},
    {"Group": "Propulsion", "Component": esc_name, "Number": int(n_esc),
     "Weight [gr]": n_esc * esc_w, "Price [€]": n_esc * esc_p},
    {"Group": "Propulsion", "Component": bat_name, "Number": 1,
     "Weight [gr]": bat_w, "Price [€]": bat_p, "_battery": True},
    {"Group": "Avionics", "Component": fc_name, "Number": 1,
     "Weight [gr]": fc_w, "Price [€]": fc_p},
]
bom += _rows_from_editor(sensors, "Avionics")
bom += _rows_from_editor(comm_air, "Avionics")
bom += _rows_from_editor(frame, "Airframe")
bom += _rows_from_editor(ground, "Ground station", offvehicle=True)

bom_df = pd.DataFrame(bom)

battery_w = sum(r["Weight [gr]"] for r in bom if r.get("_battery"))
vehicle_w = sum(r["Weight [gr]"] for r in bom if not r.get("_offvehicle"))
ground_w = sum(r["Weight [gr]"] for r in bom if r.get("_offvehicle"))
ground_p = sum(r["Price [€]"] for r in bom if r.get("_offvehicle"))
total_w = vehicle_w
weight_wo_batt = vehicle_w - battery_w
total_p = bom_df["Price [€]"].sum()

show = bom_df.drop(
    columns=[c for c in ["_battery", "_offvehicle"] if c in bom_df.columns])
show.insert(0, "No.", range(1, len(show) + 1))

# ---- Results: rendered at the TOP, inside a gray box ----
with results_area:
    st.subheader("Results")
    with st.container(border=True, key="wbox_results"):
        m = st.columns(4)
        m[0].metric("Vehicle weight w/o battery", f"{weight_wo_batt:,.0f} gr")
        m[1].metric("Vehicle total weight", f"{total_w:,.0f} gr",
                    help="On-board mass including the battery. "
                         "Excludes ground station.")
        m[2].metric("Ground station", f"{ground_w:,.0f} gr",
                    help=f"Stays on the ground — not part of flight weight. "
                         f"Cost € {ground_p:,.0f}.")
        m[3].metric("Total price", f"€ {total_p:,.0f}",
                    help="Vehicle + ground station.")
    st.divider()

# ---- Bill of materials: rendered at the BOTTOM, after the inputs ----
st.divider()
st.subheader("Bill of materials")
st.dataframe(
    show, hide_index=True, use_container_width=True,
    column_config={
        "No.": st.column_config.NumberColumn(format="%d", width="small"),
        "Weight [gr]": st.column_config.NumberColumn(format="%.0f"),
        "Price [€]": st.column_config.NumberColumn(format="%.2f"),
    })

st.caption(f"**Total:** {total_w:,.0f} gr  ·  € {total_p:,.2f}  across "
           f"{len(bom_df)} line items.")

st.download_button(
    "⬇️ Download BOM as CSV",
    data=show.to_csv(index=False).encode("utf-8"),
    file_name="bom.csv", mime="text/csv")
