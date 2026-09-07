# PMV Comfort Gauge

An interactive calculator that estimates **Predicted Mean Vote (PMV)** and
**Predicted Percentage Dissatisfied (PPD)** from Fanger's steady-state
thermal comfort model, per ISO 7730 / ASHRAE 55.

Run with:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The PMV/PPD math lives in `pmv.py`, importable on its own (`from pmv import pmv_ppd`).

## Inputs

- Air temperature
- Mean radiant temperature
- Relative air speed
- Relative humidity
- Metabolic rate (with ASHRAE 55 activity presets)
- Clothing insulation (with ASHRAE 55 ensemble presets)

## Output

- PMV score on the −3…+3 ASHRAE thermal sensation scale
- PPD (% dissatisfied)
- Skin heat balance (W/m²)
- ISO 7730 comfort category (I / II / III)
