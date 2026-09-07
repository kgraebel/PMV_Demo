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

## Nest thermostat integration (optional)

`nest.py` pulls live air temperature and relative humidity from a Nest
thermostat via Google's Smart Device Management (SDM) API, and `app.py`
has a "Pull temperature & humidity from Nest" button that fills those two
sliders from it. (Nest doesn't measure mean radiant temperature, air
speed, metabolic rate, or clothing insulation — those stay manual.)

Requires a Google [Device Access](https://developers.google.com/nest/device-access)
project (one-time $5 fee) and an OAuth client:

1. In [Google Cloud Console](https://console.cloud.google.com), enable the
   **Smart Device Management API** and create an OAuth client ID (type: Web
   application) with `https://www.google.com` as an authorized redirect URI.
2. In the [Device Access Console](https://console.nest.google.com/device-access),
   pay the one-time fee and create a project linked to that OAuth client ID.
   Its project ID is your `NEST_PROJECT_ID`.
3. Make sure your thermostat shows up in the Google Home app under the same
   account you'll authorize with.
4. Run `python3 nest_setup.py` — it walks you through the consent screen and
   writes `NEST_PROJECT_ID` / `NEST_CLIENT_ID` / `NEST_CLIENT_SECRET` /
   `NEST_REFRESH_TOKEN` straight into your local `.env` file. Run this
   yourself in your own terminal; it only talks to Google's OAuth endpoints.

Or skip the script and copy `.env.example` to `.env` by hand — **never commit
`.env`**, it holds live credentials.

Don't know your device ID? Leave `NEST_DEVICE_ID` blank and run:

```python
from nest import NestThermostat
for d in NestThermostat().list_devices():
    print(d)
```
