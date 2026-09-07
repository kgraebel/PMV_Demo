"""PMV Comfort Gauge — Streamlit rebuild of the thermal comfort calculator."""

import streamlit as st

from pmv import CLO_PRESETS, MET_PRESETS, pmv_ppd

st.set_page_config(page_title="PMV Comfort Gauge", page_icon="🌡️", layout="wide")

CSS = """
<style>
  :root{
    --paper:#EFF3F1;
    --surface:#FFFFFF;
    --surface-2:#E4EAE7;
    --ink:#16211E;
    --ink-soft:#4B5A55;
    --line:#C9D3CE;
    --accent:#2A6F6B;
    --accent-ink:#EAF5F3;
    --cold:#3E7CB1;
    --neutral-data:#6E7A70;
    --hot:#C1442A;
    --cat1:#2A6F6B;
    --cat2:#A6752B;
    --cat3:#C1442A;
    --cat-out:#9E2A1E;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --paper:#10181A;
      --surface:#17211F;
      --surface-2:#1E2A27;
      --ink:#E7F0EC;
      --ink-soft:#A8BDB6;
      --line:#2B3835;
      --accent:#4FA39D;
      --accent-ink:#06110F;
      --cold:#6FA6D6;
      --neutral-data:#93A29A;
      --hot:#E0713F;
      --cat1:#4FA39D;
      --cat2:#D6A94A;
      --cat3:#E0713F;
      --cat-out:#E2584A;
    }
  }

  @import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

  html, body, [class*="css"] { font-family: "Archivo", "Helvetica Neue", Arial, sans-serif; }
  .stApp { background: var(--paper); color: var(--ink); }
  .block-container { padding-top: 2.2rem; max-width: 1120px; }

  .mono { font-family: "IBM Plex Mono", monospace; }

  .kicker{
    font-family:"IBM Plex Mono", monospace;
    font-size:0.72rem;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:var(--ink-soft);
    margin:0 0 0.3rem;
  }
  .page-title{
    font-size:2rem;
    font-weight:700;
    margin:0 0 0.2rem;
    letter-spacing:-0.01em;
    color: var(--ink);
  }
  .standard-tag{
    font-family:"IBM Plex Mono", monospace;
    font-size:0.75rem;
    color:var(--ink-soft);
    line-height:1.5;
  }
  hr.header-rule{ border: none; border-top: 1px solid var(--line); margin: 0.6rem 0 1.6rem; }

  div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stVerticalBlock"]) {
    background: var(--surface);
    border-radius: 10px;
    box-shadow: 0 1px 2px rgba(20,32,29,0.06), 0 8px 24px -12px rgba(20,32,29,0.18);
  }
  div[data-testid="stVerticalBlockBorderWrapper"] > div { border-color: var(--line) !important; border-radius: 10px !important; }

  .panel{
    background:var(--surface);
    border:1px solid var(--line);
    border-radius:10px;
    padding: 1.4rem;
    box-shadow: 0 1px 2px rgba(20,32,29,0.06), 0 8px 24px -12px rgba(20,32,29,0.18);
  }
  .panel-title{
    font-size:0.95rem;
    font-weight:600;
    color: var(--ink);
    margin-bottom: 1rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--line);
  }

  .result-hero{ text-align:center; padding-bottom: 1.1rem; border-bottom:1px solid var(--line); margin-bottom: 1.2rem; }
  .pmv-value{
    font-family:"IBM Plex Mono", monospace;
    font-size:3.2rem;
    font-weight:600;
    line-height:1;
    color: var(--ink);
  }
  .pmv-caption{
    font-size:0.75rem;
    color:var(--ink-soft);
    margin-top:0.5rem;
    font-family:"IBM Plex Mono", monospace;
    letter-spacing:0.02em;
  }
  .sensation-label{
    display:inline-block;
    margin-top:0.7rem;
    font-size:0.95rem;
    font-weight:600;
    padding:0.3rem 0.85rem;
    border-radius:999px;
    background:var(--surface-2);
    color: var(--ink);
  }

  .gauge-track{
    position:relative;
    height:32px;
    border-radius:6px;
    background: linear-gradient(to right, var(--cold) 0%, var(--neutral-data) 50%, var(--hot) 100%);
    margin-bottom:0.35rem;
  }
  .gauge-marker{
    position:absolute;
    top:-6px;
    width:2px;
    height:44px;
    background:var(--ink);
  }
  .gauge-ticks, .gauge-words{ display:flex; justify-content:space-between; }
  .gauge-ticks span{ font-family:"IBM Plex Mono", monospace; font-size:0.62rem; color:var(--ink-soft); width:14.28%; text-align:center; }
  .gauge-words span{ font-size:0.6rem; color:var(--ink-soft); width:14.28%; text-align:center; }

  .metrics-row{ display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--line); border:1px solid var(--line); border-radius:8px; overflow:hidden; margin-top:1.2rem; }
  .metric-tile{ background:var(--surface); padding:0.8rem 1rem; }
  .metric-tile .k{ font-size:0.66rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--ink-soft); font-weight:600; }
  .metric-tile .v{ font-family:"IBM Plex Mono", monospace; font-size:1.25rem; font-weight:600; color: var(--ink); margin-top:0.1rem; }

  .category-strip{ margin-top:1rem; padding:0.75rem 1rem; border-radius:8px; border:1px solid var(--line); background:var(--surface-2); display:flex; align-items:center; gap:0.7rem; }
  .category-dot{ width:10px; height:10px; border-radius:50%; flex:none; }
  .category-text{ font-size:0.78rem; color:var(--ink-soft); line-height:1.4; }
  .category-text strong{ color:var(--ink); }

  .about{ margin-top:1.1rem; padding-top:1.1rem; font-size:0.8rem; color:var(--ink-soft); line-height:1.6; border-top:1px solid var(--line); }
  .about strong{ color:var(--ink); }

  .field-name{ font-size: 0.85rem; font-weight: 600; color: var(--ink); }
  .field-sym{ color: var(--ink-soft); font-family:"IBM Plex Mono", monospace; font-weight:500; font-size:0.76rem; }

  div[data-testid="stSlider"] { padding-top: 0.1rem; }
  button[kind="secondary"]{ font-size: 0.72rem !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

DEFAULTS = {"ta": 24.0, "tr": 24.0, "vel": 0.1, "rh": 50.0, "met": 1.1, "clo": 0.61}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def set_val(key, val):
    st.session_state[key] = val


st.markdown(
    """
    <p class="kicker">Thermal comfort · Fanger model</p>
    <div style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:1rem;">
      <h1 class="page-title">Predicted Mean Vote calculator</h1>
      <div class="standard-tag">ISO 7730 · ASHRAE 55<br>six-parameter steady-state model</div>
    </div>
    <hr class="header-rule">
    """,
    unsafe_allow_html=True,
)

col_left, col_right = st.columns([1.05, 0.95], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown('<div class="panel-title">Room &amp; occupant inputs</div>', unsafe_allow_html=True)

        st.markdown('<span class="field-name">Air temperature <span class="field-sym">t&#8320;</span></span>', unsafe_allow_html=True)
        ta = st.slider("Air temperature", 10.0, 40.0, step=0.1, key="ta", label_visibility="collapsed", format="%.1f °C")

        st.markdown('<span class="field-name">Mean radiant temperature <span class="field-sym">t&#7523;</span></span>', unsafe_allow_html=True)
        tr = st.slider("Mean radiant temperature", 10.0, 40.0, step=0.1, key="tr", label_visibility="collapsed", format="%.1f °C")

        st.markdown('<span class="field-name">Air speed, relative <span class="field-sym">v</span></span>', unsafe_allow_html=True)
        vel = st.slider("Air speed", 0.0, 2.0, step=0.01, key="vel", label_visibility="collapsed", format="%.2f m/s")

        st.markdown('<span class="field-name">Relative humidity <span class="field-sym">RH</span></span>', unsafe_allow_html=True)
        rh = st.slider("Relative humidity", 0.0, 100.0, step=1.0, key="rh", label_visibility="collapsed", format="%.0f %%")

        st.markdown('<span class="field-name">Metabolic rate <span class="field-sym">M</span></span>', unsafe_allow_html=True)
        met = st.slider("Metabolic rate", 0.7, 4.0, step=0.05, key="met", label_visibility="collapsed", format="%.2f met")
        for row_start in range(0, len(MET_PRESETS), 3):
            row = MET_PRESETS[row_start:row_start + 3]
            for c, (label, val) in zip(st.columns(3), row):
                c.button(label, key=f"met_{val}", on_click=set_val, args=("met", val), use_container_width=True)

        st.markdown('<span class="field-name">Clothing insulation <span class="field-sym">I&#7580;&#7517;</span></span>', unsafe_allow_html=True)
        clo = st.slider("Clothing insulation", 0.0, 2.0, step=0.01, key="clo", label_visibility="collapsed", format="%.2f clo")
        for row_start in range(0, len(CLO_PRESETS), 3):
            row = CLO_PRESETS[row_start:row_start + 3]
            for c, (label, val) in zip(st.columns(3), row):
                c.button(label, key=f"clo_{val}", on_click=set_val, args=("clo", val), use_container_width=True)

result = pmv_ppd(
    st.session_state.ta, st.session_state.tr, st.session_state.vel,
    st.session_state.rh, st.session_state.met, st.session_state.clo,
)

pmv_clamped = max(-3.5, min(3.5, result.pmv))
marker_pct = max(0, min(100, ((pmv_clamped + 3) / 6) * 100))
cat_var = {"Category I": "cat1", "Category II": "cat2", "Category III": "cat3", "Outside range": "cat-out"}[result.category]

with col_right:
    st.markdown(
        f"""
        <div class="panel">
          <div class="result-hero">
            <div class="pmv-value">{result.pmv:+.2f}</div>
            <p class="pmv-caption">PREDICTED MEAN VOTE · &minus;3 TO +3</p>
            <span class="sensation-label">{result.sensation}</span>
          </div>

          <div class="gauge-track"><div class="gauge-marker" style="left:{marker_pct:.2f}%"></div></div>
          <div class="gauge-ticks"><span>&minus;3</span><span>&minus;2</span><span>&minus;1</span><span>0</span><span>+1</span><span>+2</span><span>+3</span></div>
          <div class="gauge-words"><span>Cold</span><span>Cool</span><span>Sl. cool</span><span>Neutral</span><span>Sl. warm</span><span>Warm</span><span>Hot</span></div>

          <div class="metrics-row">
            <div class="metric-tile"><div class="k">Dissatisfied</div><div class="v">{result.ppd:.1f}%</div></div>
            <div class="metric-tile"><div class="k">Skin heat balance</div><div class="v">{result.balance:+.1f} W/m²</div></div>
          </div>

          <div class="category-strip">
            <div class="category-dot" style="background:var(--{cat_var})"></div>
            <div class="category-text"><strong>{result.category}</strong> — {result.category_desc}</div>
          </div>

          <div class="about">
            <strong>PMV</strong> predicts the mean thermal-sensation vote of a large population on the ASHRAE
            7-point scale, from a steady-state heat balance of the human body (Fanger, 1970).
            <strong>PPD</strong> converts that vote into the percentage of people expected to be dissatisfied,
            even at PMV&nbsp;=&nbsp;0 at least 5% remain unsatisfied.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    '<p class="mono" style="text-align:center; font-size:0.68rem; color:var(--ink-soft); margin-top:1.5rem;">'
    "Fanger heat-balance iteration · ISO 7730:2005 Annex D reference algorithm</p>",
    unsafe_allow_html=True,
)
