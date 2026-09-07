# PMV Comfort Gauge

An interactive calculator that estimates **Predicted Mean Vote (PMV)** and
**Predicted Percentage Dissatisfied (PPD)** from Fanger's steady-state
thermal comfort model, per ISO 7730 / ASHRAE 55.

Open `index.html` in a browser — everything runs client-side, no build step.

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
