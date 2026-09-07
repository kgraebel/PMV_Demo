"""Fanger PMV/PPD thermal comfort model — ISO 7730:2005 Annex D reference algorithm."""

import math
from dataclasses import dataclass

SENSATIONS = ["Cold", "Cool", "Slightly cool", "Neutral", "Slightly warm", "Warm", "Hot"]


def c_to_f(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def f_to_c(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9

MET_PRESETS = [
    ("Reclining", 0.8),
    ("Seated", 1.0),
    ("Typing", 1.1),
    ("Standing", 1.2),
    ("Walking", 2.0),
    ("Heavy work", 3.4),
]

CLO_PRESETS = [
    ("Shorts & tee", 0.36),
    ("Short sleeve", 0.57),
    ("Shirt & pants", 0.61),
    ("Business suit", 1.0),
    ("Suit + sweater", 1.3),
    ("Heavy wool", 1.5),
]


@dataclass
class PmvResult:
    pmv: float
    ppd: float
    balance: float
    sensation: str
    category: str
    category_desc: str


def pmv_ppd(ta: float, tr: float, vel: float, rh: float, met: float, clo: float, wme: float = 0.0) -> PmvResult:
    """Compute Predicted Mean Vote and Predicted Percentage Dissatisfied.

    ta, tr: air / mean radiant temperature (°C)
    vel: relative air speed (m/s)
    rh: relative humidity (%)
    met: metabolic rate (met)
    clo: clothing insulation (clo)
    wme: external work (met), usually 0
    """
    pa = rh * 10 * math.exp(16.6536 - 4030.183 / (ta + 235))

    icl = 0.155 * clo
    m = met * 58.15
    w = wme * 58.15
    mw = m - w

    fcl = 1 + 1.29 * icl if icl <= 0.078 else 1.05 + 0.645 * icl

    hcf = 12.1 * math.sqrt(vel)
    hc = hcf
    taa = ta + 273
    tra = tr + 273
    tcla = taa + (35.5 - ta) / (3.5 * icl + 0.1)

    p1 = icl * fcl
    p2 = p1 * 3.96
    p3 = p1 * 100
    p4 = p1 * taa
    p5 = (308.7 - 0.028 * mw) + p2 * (tra / 100) ** 4

    xn = tcla / 100
    xf = tcla / 50
    eps = 0.00015
    n = 0

    while abs(xn - xf) > eps and n < 150:
        xf = (xf + xn) / 2
        hcn = 2.38 * abs(100 * xf - taa) ** 0.25
        hc = hcf if hcf > hcn else hcn
        xn = (p5 + p4 * hc - p2 * xf ** 4) / (100 + p3 * hc)
        n += 1

    tcl = 100 * xn - 273

    hl1 = 3.05 * 0.001 * (5733 - 6.99 * mw - pa)
    hl2 = 0.42 * (mw - 58.15) if mw > 58.15 else 0
    hl3 = 1.7 * 0.00001 * m * (5867 - pa)
    hl4 = 0.0014 * m * (34 - ta)
    hl5 = 3.96 * fcl * (xn ** 4 - (tra / 100) ** 4)
    hl6 = fcl * hc * (tcl - ta)

    ts = 0.303 * math.exp(-0.036 * m) + 0.028
    balance = mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6
    pmv = ts * balance
    ppd = 100 - 95 * math.exp(-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2)

    idx = round(min(3, max(-3, pmv))) + 3
    sensation = SENSATIONS[idx]

    abs_pmv = abs(pmv)
    if abs_pmv <= 0.2 and ppd < 6:
        category, category_desc = "Category I", "meets the tightest comfort tolerance (PPD < 6%)."
    elif abs_pmv <= 0.5 and ppd < 10:
        category, category_desc = "Category II", "meets the normal design tolerance (PPD < 10%)."
    elif abs_pmv <= 0.7 and ppd < 15:
        category, category_desc = "Category III", "meets the relaxed acceptable tolerance (PPD < 15%)."
    else:
        category, category_desc = "Outside range", "exceeds ISO 7730's acceptable PPD tolerances."

    return PmvResult(pmv=pmv, ppd=ppd, balance=balance, sensation=sensation,
                      category=category, category_desc=category_desc)
