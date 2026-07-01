# JOSELITO — Drone Design Dashboard

Interactive Streamlit dashboard for the JOSELITO tail-sitter drone's
longitudinal steady-trim & thrust-feasibility model (2-DOF).

Pitch angle γ: **90° = hover**, **0° = forward cruise**.
Trim: `L = W·cosγ`, `v² = W·cosγ / kL`, `T = D + L·tanγ`.

## Run locally

```bash
pip install -r requirements.txt
streamlit run drone_design_dashboard.py
```

Opens at http://localhost:8501.

## Deploy (public URL)

Hosted free on [Streamlit Community Cloud](https://share.streamlit.io):
1. Push this folder to a GitHub repo.
2. On share.streamlit.io → **New app** → pick the repo, branch `main`,
   main file `drone_design_dashboard.py`.
3. Deploy → you get a public `https://<name>.streamlit.app` URL.

> ⚠️ Default aero coefficients (C_L0, C_D0) are placeholders. Replace with
> real airfoil/CFD values before treating results as authoritative.
