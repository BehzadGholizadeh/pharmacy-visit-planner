"""
Visit time model: city size class (by population), traffic speed, visit time inside the pharmacy,
and estimated travel distance between consecutive visits.

Every number here is an adjustable assumption; change it in the tables below.
"""
import numpy as np
import pandas as pd

ROAD_FACTOR = 1.35          # straight-line distance -> road distance
INTERCITY_SPEED = 60        # km/h between towns of one territory
SERVICE_CROWDED = 30        # minutes inside the pharmacy in a big city / crowded area
SERVICE_QUIET = 20          # minutes inside the pharmacy in a quiet area / low population density
TEHRAN_SPEED = 13           # average speed in Tehran traffic (km/h)

# min population, class, speed km/h in traffic, density (people/km²), parking+walking per visit (min), crowded?
CLASSES = [
    (1_000_000, "کلان‌شهر", 17, 10000, 7, True),
    (250_000, "شهر بزرگ", 22, 7000, 5, True),
    (50_000, "شهر متوسط", 27, 5000, 3, None),   # None: depends on the neighborhood
    (0, "شهر کوچک / روستا", 32, 3500, 2, False),
]


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def city_profiles(df, pop):
    """One row per (province, county, city): population, class, speed, area, average distance between
    nearby pharmacies (Beardwood–Halton–Hammersley estimate 0.7124·√(A/N)), and the start-of-day commute."""
    keys = ["province", "county", "city"]
    g = df.groupby(keys).agg(records=("gln", "size"), n_nbh=("neighborhood", "nunique")).reset_index()
    g = g.merge(pop[keys + ["population", "lat", "lon"]], on=keys, how="left")
    # Unknown population: estimated from the national ratio of population to the number of records
    ratio = (g.population / g.records).median()
    g["population_estimated"] = g.population.isna()
    g["population"] = g.population.fillna(g.records * ratio).round()
    cls = [next(c for c in CLASSES if p >= c[0]) for p in g.population]
    g["city_class"] = [c[1] for c in cls]
    g["speed_kmh"] = [TEHRAN_SPEED if city == "تهران" else c[2] for city, c in zip(g.city, cls)]
    g["area_km2"] = [max(1.0, p / c[3]) for p, c in zip(g.population, cls)]
    g["parking_min"] = [c[4] for c in cls]
    g["crowded_rule"] = [c[5] for c in cls]
    g["hop_km"] = np.maximum(0.2, 0.7124 * np.sqrt(g.area_km2 / g.records)) * ROAD_FACTOR
    g["nbh_hop_km"] = np.maximum(g.hop_km, 0.5 * np.sqrt(g.area_km2 / g.n_nbh) * ROAD_FACTOR)
    g["commute_km"] = 0.35 * np.sqrt(g.area_km2) * ROAD_FACTOR     # from home to the first visit
    return g


def service_minutes(df, prof):
    """30 minutes in big cities and crowded neighborhoods, 20 minutes in quiet areas. In a medium city a
    neighborhood counts as crowded when its number of centers is in the top quarter of that city
    (commercial area / city center)."""
    keys = ["province", "county", "city"]
    d = df.merge(prof[keys + ["crowded_rule"]], on=keys, how="left")
    nb = d.groupby(keys + ["neighborhood"])["gln"].transform("size")
    q75 = nb.groupby([d[k] for k in keys]).transform(lambda s: max(4, s.quantile(0.75)))
    crowded = d.crowded_rule.where(d.crowded_rule.notna(), nb >= q75).astype(bool)
    return pd.Series(np.where(crowded, SERVICE_CROWDED, SERVICE_QUIET), index=df.index), \
        pd.Series(crowded.values, index=df.index)


def est_minutes_per_visit(prof_row, service):
    """For estimating territory size: visit + travel to the next visit + parking."""
    return service + prof_row.hop_km / prof_row.speed_kmh * 60 + prof_row.parking_min


class DayClock:
    """Running total of one day's time while visits are added."""

    def __init__(self, prof, base, geo):
        # town -> row (a dict lookup is much faster than .loc in the loop)
        self.prof = dict(zip(prof.index, prof.itertuples(index=False)))
        self.base, self.geo = base, geo

    def leg(self, prev, cur):
        """Travel minutes and km from the previous visit (or from home/base) to the current one."""
        P = self.prof[cur["_town"]]
        if prev is None:
            B = self.prof[self.base]
            if cur["_town"] == self.base:
                km, spd = P.commute_km, P.speed_kmh
            else:
                inter = haversine_km(B.lat, B.lon, P.lat, P.lon) * ROAD_FACTOR
                inter = 15.0 if not np.isfinite(inter) or inter < 1 else inter
                return inter / INTERCITY_SPEED * 60 + P.parking_min, inter
        elif prev["_town"] != cur["_town"]:
            Q = self.prof[prev["_town"]]
            inter = haversine_km(Q.lat, Q.lon, P.lat, P.lon) * ROAD_FACTOR
            inter = 15.0 if not np.isfinite(inter) or inter < 1 else inter
            return inter / INTERCITY_SPEED * 60 + P.parking_min, inter
        elif self.geo and np.isfinite(prev["lat"]) and np.isfinite(cur["lat"]):
            km = max(0.2, haversine_km(prev["lat"], prev["lon"], cur["lat"], cur["lon"]) * ROAD_FACTOR)
            spd = P.speed_kmh
        else:
            km = P.nbh_hop_km if prev["neighborhood"] != cur["neighborhood"] else P.hop_km
            spd = P.speed_kmh
        return km / spd * 60 + P.parking_min, km


def build_days(rows, clock, budget):
    """Greedy: in the given (hierarchy) order, add visits to the day while travel+visit time fits the budget.
    If the town changes and less than 20% of the day is left, a new day starts."""
    days, cur, used, prev = [], [], 0.0, None
    for r in rows:
        t, _ = clock.leg(prev, r)
        town_change = prev is not None and prev["_town"] != r["_town"]
        if cur and (used + t + r["service_min"] > budget or (town_change and budget - used < 0.2 * budget)):
            days.append(cur)
            cur, used, prev = [], 0.0, None
            t, _ = clock.leg(None, r)
        cur.append(r)
        used += t + r["service_min"]
        prev = r
    if cur:
        days.append(cur)
    return days


def day_schedule(day, clock, start_min):
    """Arrival time, travel and visit time of each stop in one day."""
    out, t, prev = [], start_min, None
    for r in day:
        tm, km = clock.leg(prev, r)
        t += tm
        out.append({"travel_min": round(tm), "travel_km": round(km, 1), "arrive_min": t,
                    "leave_min": t + r["service_min"]})
        t += r["service_min"]
        prev = r
    return out


def hhmm(m):
    m = int(round(m))
    return f"{m // 60:02d}:{m % 60:02d}"

