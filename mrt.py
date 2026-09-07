"""Estimates a room's mean radiant temperature (MRT) from outdoor conditions
and the room's construction, using a simplified steady-state heat-balance
model -- not a full radiant/view-factor simulation.

Method:
1. Each bounding surface's interior temperature is estimated from
   steady-state 1D conduction between indoor and outdoor air:

       Ts = Ti - (Ti - To) * (Rsi / (Rsi + R))

   where Rsi is the standard still-air interior surface film resistance
   (ASHRAE Fundamentals) and R is that surface's assembly R-value. A
   surface not exposed to outdoor air is left at the indoor air temperature.
2. MRT is taken as the area-weighted average of all surface temperatures --
   the standard simplified MRT definition (ASHRAE Fundamentals) for a
   roughly-centered occupant, used when detailed radiant exchange isn't
   computed.

Units are US customary throughout (feet, Fahrenheit, R-value in
ft^2*F*h/Btu) to match how these are normally quoted to a homeowner.

Simplifying assumptions:
- The room is a simple box (length x width x height).
- Exterior walls are treated as an even share of the four walls (e.g.
  2 of 4 exterior walls == half the wall area), not specific wall lengths.
- Windows sit on exterior walls.
- Surfaces not exposed to outdoor air (interior walls, a floor over
  conditioned space, etc.) are assumed to stay at the indoor air temperature.
"""

from dataclasses import dataclass, field
from typing import List

# ASHRAE Fundamentals: still-air interior surface film resistance, ft^2*F*h/Btu
R_SI_WALL = 0.68     # vertical surface, horizontal heat flow
R_SI_CEILING = 0.61  # horizontal surface, heat flow up
R_SI_FLOOR = 0.92    # horizontal surface, heat flow down

WALL_R_PRESETS = [
    ("Uninsulated (older home)", 4.0),
    ("Standard 2x4, R-13", 13.0),
    ("Well insulated 2x6, R-21", 21.0),
]
CEILING_R_PRESETS = [
    ("Minimal attic insulation", 19.0),
    ("Standard attic, R-38", 38.0),
    ("High-performance, R-49", 49.0),
]
FLOOR_R_PRESETS = [
    ("Uninsulated slab/crawlspace", 5.0),
    ("Standard, R-19", 19.0),
    ("Well insulated, R-30", 30.0),
]
WINDOW_R_PRESETS = [
    ("Single pane", 1.0),
    ("Double pane", 2.0),
    ("Double pane, low-E", 3.3),
    ("Triple pane", 5.0),
]


@dataclass
class SurfaceTemp:
    name: str
    area_ft2: float
    temperature_f: float
    exposed_to_outside: bool


@dataclass
class MRTEstimate:
    mrt_f: float
    surfaces: List[SurfaceTemp] = field(default_factory=list)


class RoomMRTEstimator:
    def __init__(
        self,
        length_ft: float,
        width_ft: float,
        height_ft: float,
        exterior_walls: int = 1,
        ceiling_exposed: bool = False,
        floor_exposed: bool = False,
        window_area_ft2: float = 0.0,
        wall_r_value: float = 13.0,
        ceiling_r_value: float = 38.0,
        floor_r_value: float = 25.0,
        window_r_value: float = 2.0,
    ):
        if length_ft <= 0 or width_ft <= 0 or height_ft <= 0:
            raise ValueError("Room dimensions must be positive")
        if not (0 <= exterior_walls <= 4):
            raise ValueError("exterior_walls must be between 0 and 4")
        if window_area_ft2 < 0:
            raise ValueError("window_area_ft2 cannot be negative")

        self.length_ft = length_ft
        self.width_ft = width_ft
        self.height_ft = height_ft
        self.exterior_walls = exterior_walls
        self.ceiling_exposed = ceiling_exposed
        self.floor_exposed = floor_exposed
        self.window_area_ft2 = window_area_ft2
        self.wall_r_value = wall_r_value
        self.ceiling_r_value = ceiling_r_value
        self.floor_r_value = floor_r_value
        self.window_r_value = window_r_value

    @staticmethod
    def _surface_temp(indoor_f: float, outside_f: float, r_si: float, r_value: float) -> float:
        r_total = r_si + r_value
        return indoor_f - (indoor_f - outside_f) * (r_si / r_total)

    def estimate(self, indoor_air_temp_f: float, outside_temp_f: float) -> MRTEstimate:
        floor_area = self.length_ft * self.width_ft
        ceiling_area = self.length_ft * self.width_ft
        wall_area_gross = 2 * (self.length_ft + self.width_ft) * self.height_ft
        window_area = min(self.window_area_ft2, wall_area_gross)

        ext_fraction = self.exterior_walls / 4
        ext_wall_area = max(wall_area_gross * ext_fraction - window_area, 0.0)
        int_wall_area = wall_area_gross * (1 - ext_fraction)

        surfaces: List[SurfaceTemp] = []

        def add(name, area, exposed, r_si, r_value):
            if area <= 0:
                return
            temperature = (
                self._surface_temp(indoor_air_temp_f, outside_temp_f, r_si, r_value)
                if exposed else indoor_air_temp_f
            )
            surfaces.append(SurfaceTemp(name, area, temperature, exposed))

        add("Exterior walls", ext_wall_area, True, R_SI_WALL, self.wall_r_value)
        add("Interior walls", int_wall_area, False, R_SI_WALL, self.wall_r_value)
        add("Windows", window_area, True, R_SI_WALL, self.window_r_value)
        add("Ceiling", ceiling_area, self.ceiling_exposed, R_SI_CEILING, self.ceiling_r_value)
        add("Floor", floor_area, self.floor_exposed, R_SI_FLOOR, self.floor_r_value)

        total_area = sum(s.area_ft2 for s in surfaces)
        if total_area <= 0:
            raise ValueError("Room has no surface area to estimate from")

        mrt = sum(s.area_ft2 * s.temperature_f for s in surfaces) / total_area
        return MRTEstimate(mrt_f=mrt, surfaces=surfaces)
