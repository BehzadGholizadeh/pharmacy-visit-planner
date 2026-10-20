"""
Step 2: cluster each city into visitor territories and daily routes, and order the visits.

    python plan_routes.py                                   # both versions (pharmacies only / all centers)
    python plan_routes.py --hours 9 --days-per-week 5 --weeks 4

Capacity is time-based: each day is 9 hours (minus a break), filled with travel time (by city size
and traffic, see timing.py) plus time inside the pharmacy (30 minutes crowded / 20 minutes quiet).

If work/geocode.csv (output of geocode_neshan.py) exists, the geographic mode runs:
balanced k-means + a shortest path (nearest neighbor + 2-opt) on real coordinates.
Otherwise the offline mode runs on the 10-digit postal code (a hierarchical stand-in for location).
"""
import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from timing import (CLASSES, DayClock, build_days, city_profiles, day_schedule, haversine_km, hhmm,
                    service_minutes)

ROOT = Path(__file__).parent
WORK = ROOT / "work"
OUT = ROOT / "output"
IRAN_BBOX = (24.0, 40.5, 43.5, 63.8)   # lat_min, lat_max, lon_min, lon_max
ROAD_FACTOR = 1.35                      # straight-line distance -> approximate city road distance


# ---------------------------------------------------------------- geometry
def to_xy(lat, lon):
    """Local projection to kilometers (accurate enough within a single city)."""
    lat0 = np.radians(np.nanmean(lat))
    return np.column_stack([np.radians(lon) * 6371 * np.cos(lat0), np.radians(lat) * 6371])


def hilbert_index(lat, lon, order=16):
    """Position on a Hilbert curve: points close on the curve are close on the map."""
    n = 1 << order
    x = ((lon - lon.min()) / max(np.ptp(lon), 1e-9) * (n - 1)).astype(np.int64)
    y = ((lat - lat.min()) / max(np.ptp(lat), 1e-9) * (n - 1)).astype(np.int64)
    d = np.zeros(len(x), np.int64)
    s = n // 2
    while s > 0:
        rx = (x & s) > 0
        ry = (y & s) > 0
        d += s * s * ((3 * rx) ^ ry)
        flip = ~ry
        x, y = np.where(flip & rx, s - 1 - x, x), np.where(flip & rx, s - 1 - y, y)
        x, y = np.where(flip, y, x), np.where(flip, x, y)
        s //= 2
    return d


def path_len(xy, order):
    p = xy[order]
    return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()) if len(p) > 1 else 0.0


def tsp_open(xy, start=None):
    """Open path (no return to the start): nearest neighbor from every start point, then 2-opt."""
    n = len(xy)
    if n <= 2:
        return list(range(n))
    D = np.linalg.norm(xy[:, None] - xy[None], axis=2)
    best = None
    for s in ([start] if start is not None else range(n)):
        order, left = [s], set(range(n)) - {s}
        while left:
            nxt = min(left, key=lambda j: D[order[-1], j])
            order.append(nxt); left.remove(nxt)
        order = two_opt(order, D, fixed_start=start is not None)
        L = sum(D[a, b] for a, b in zip(order, order[1:]))
        if best is None or L < best[0]:
            best = (L, order)
    return best[1]


def two_opt(order, D, fixed_start=False):
    improved, n = True, len(order)
    while improved:
        improved = False
        for i in range(1 if fixed_start else 0, n - 1):
            for k in range(i + 1, n):
                a = D[order[i - 1], order[i]] if i > 0 else 0
                b = D[order[k], order[k + 1]] if k < n - 1 else 0
                c = D[order[i - 1], order[k]] if i > 0 else 0
                d = D[order[i], order[k + 1]] if k < n - 1 else 0
                if c + d < a + b - 1e-9:
                    order[i:k + 1] = order[i:k + 1][::-1]
                    improved = True
    return order


def balanced_kmeans(xy, k, cap, iters=15, seed=0):
    """K-means with a capacity limit per cluster (no cluster gets more than cap points)."""
    n = len(xy)
    if k <= 1:
        return np.zeros(n, int)
    C = KMeans(k, n_init=5, random_state=seed).fit(xy).cluster_centers_
    lab = None
    for _ in range(iters):
        D = np.linalg.norm(xy[:, None] - C[None], axis=2)
        # Points with the largest "regret" (difference between the best and second-best center) pick first
        srt = np.sort(D, axis=1)
        prio = np.argsort(-(srt[:, 1] - srt[:, 0]))
        size, new = np.zeros(k, int), np.empty(n, int)
        for i in prio:
            for c in np.argsort(D[i]):
                if size[c] < cap:
                    new[i] = c; size[c] += 1; break
        if lab is not None and (new == lab).all():
            break
        lab = new
        C = np.array([xy[lab == c].mean(0) if (lab == c).any() else C[c] for c in range(k)])
    return lab


# ---------------------------------------------------------------- postal (offline) mode
def postal_cuts(codes, k, cap, win=None):
    """Split the sorted keys into k contiguous parts of at most cap each; cut where the key
    changes at the highest level (county > city > neighborhood > postal code)."""
    n = len(codes)
    if k <= 1:
        return np.zeros(n, int)
    cuts, s = [], 0
    for j in range(1, k):
        left = k - j                                    # parts that remain after this one
        t = s + round((n - s) / (left + 1))
        w = win if win is not None else max(0, int(0.12 * (n - s) / (left + 1)))
        lo = max(s + 1, t - w, n - cap * left)        # leave no more than the remaining parts can hold
        hi = min(s + cap, t + w, n - left)
        best, bscore = min(max(t, lo), hi), -1
        for p in range(lo, hi + 1):
            a, b = codes[p - 1], codes[p]
            common = next((i for i in range(len(a)) if i >= len(b) or a[i] != b[i]), len(a))
            score = (len(a) - common) * 1000 - abs(p - t)   # shorter common prefix = better boundary
            if score > bscore:
                best, bscore = p, score
        cuts.append(best)
        s = best
    lab = np.zeros(n, int)
    for c in cuts:
        lab[c:] += 1
    return lab


# ---------------------------------------------------------------- coordinates
def attach_coords(df, path):
    if not path.exists():
        df["lat"] = df["lon"] = np.nan
        df["coord_source"] = ""
        return df
    g = pd.read_csv(path, dtype={"gln": str}).drop_duplicates("gln", keep="last")
    df = df.merge(g[["gln", "lat", "lon"]], on="gln", how="left")
    lat0, lat1, lon0, lon1 = IRAN_BBOX
    bad = ~df.lat.between(lat0, lat1) | ~df.lon.between(lon0, lon1)
    # A point more than 40 km from the city median is considered a geocoding error
    med = df[~bad].groupby(["province", "city"])[["lat", "lon"]].transform("median")
    far = (np.hypot(df.lat - med.lat, (df.lon - med.lon) * 0.8) * 111) > 40
    df.loc[bad | far, ["lat", "lon"]] = np.nan
    df["coord_source"] = np.where(df.lat.notna(), "geocode", "")
    # Validation with the postal code: a point that is far from its postal-code neighbors
    # (same 6 or 5 digits, at least 3 points) is replaced with the median of those neighbors
    for k, km in ((6, 2.5), (5, 5.0)):
        ok = df.coord_source == "geocode"
        grp = df[ok].groupby(df.postal.str[:k])
        med = grp[["lat", "lon"]].transform("median")
        cnt = grp["lat"].transform("size")
        dist = np.hypot(df.lat - med.lat, (df.lon - med.lon) * 0.8) * 111
        bad_pc = (dist > km) & (cnt >= 3)
        idx = bad_pc[bad_pc].index
        df.loc[idx, ["lat", "lon"]] = med.loc[idx, ["lat", "lon"]].values
        df.loc[idx, "coord_source"] = f"corrected by postal ({k} digits)"
    # Impute: average of geocoded points sharing the longest postal-code prefix (at least 5 digits)
    for k in (8, 7, 6, 5):
        m = df.lat.isna() & df.postal_valid
        if not m.any():
            break
        ref = df[df.coord_source.str.startswith(("geocode", "corrected"))].groupby(df.postal.str[:k])[["lat", "lon"]].mean()
        hit = df.loc[m, "postal"].str[:k].map(ref.lat)
        idx = hit.dropna().index
        df.loc[idx, "lat"] = hit[idx]
        df.loc[idx, "lon"] = df.loc[idx, "postal"].str[:k].map(ref.lon)
        df.loc[idx, "coord_source"] = f"postal_{k}"
    # Last resort: city center (if the city has at least one geocoded point)
    cm = df[df.coord_source == "geocode"].groupby(["province", "city"])[["lat", "lon"]].median()
    m = df.lat.isna()
    key = pd.MultiIndex.from_frame(df.loc[m, ["province", "city"]])
    df.loc[m, "lat"] = cm.lat.reindex(key).values
    df.loc[m, "lon"] = cm.lon.reindex(key).values
    df.loc[m & df.lat.notna(), "coord_source"] = "city_center"
    return df


# ---------------------------------------------------------------- planning
def hierarchy_key(df):
    """Sort key province > county > city > neighborhood > postal code. Ranks at each level follow the
    median valid postal code of that unit (a geographic stand-in), so neighboring units fall next to each other."""
    d = df.copy()
    d["_pc"] = pd.to_numeric(d["postal"].where(d["postal_valid"]), errors="coerce")
    levels = [["province", "county"], ["province", "county", "city"],
              ["province", "county", "city", "neighborhood"]]
    parts = []
    for lv, width in zip(levels, (3, 3, 4)):
        med = d.groupby(lv)["_pc"].transform("median").fillna(9e9)
        r = med.groupby([d[c] for c in lv[:-1]]).rank(method="dense").astype(int)
        parts.append(r.map(("{:0%dd}" % width).format))
    pc = d["postal"].where(d["postal_valid"], "9999999999")
    return parts[0] + parts[1] + parts[2] + pc


def pack(units, cap):
    """Pack an ordered list of (name, size) units into contiguous groups of at most cap, balanced."""
    total = sum(n for _, n in units)
    target = total / max(1, math.ceil(total / cap))
    groups, cur, load = [], [], 0
    for name, n in units:
        if cur and (load + n > cap or load >= target):
            groups.append(cur); cur, load = [], 0
        cur.append(name); load += n
    if cur:
        groups.append(cur)
    return groups


MAX_RADIUS_KM = 60          # farthest town of a territory from its main town (daily return trip)


def build_territories(df, cap, towns):
    """Territories in the hierarchy province > county > city, with geographic limits:
    1) a city whose workload is at least 75% of one visitor -> its own territory («شهر X»)
    2) small towns of a county -> geographic groups around the biggest town (radius MAX_RADIUS_KM)
    3) a small group (< 50% of capacity) -> joins the nearest group/big city of the same county, else
       of a neighboring county in the same province, if it is within the radius and capacity
    Workload = estimated minutes (_work); towns has town coordinates (_tlat/_tlon)."""
    keys = ["province", "county", "city"]
    t = (df.groupby(keys)["_work"].sum().rename("work").reset_index()
         .merge(towns, on=keys, how="left"))
    t["lat"] = t["lat"].fillna(t.groupby(["province", "county"])["lat"].transform("mean"))
    t["lon"] = t["lon"].fillna(t.groupby(["province", "county"])["lon"].transform("mean"))
    def dist(a, b):
        if np.isfinite([a.lat, a.lon, b.lat, b.lon]).all():
            return haversine_km(a.lat, a.lon, b.lat, b.lon)
        return 0.0 if a.county == b.county else 1e6     # no coordinates: only within the same county

    groups = []                                          # dict(towns=[idx], work, base=idx, big)
    for i in t.index[t.work >= cap * 0.75]:
        groups.append({"towns": [i], "work": t.work[i], "base": i, "big": True})
    for (p, c), gc in t[t.work < cap * 0.75].groupby(["province", "county"]):
        left = list(gc.sort_values("work", ascending=False).index)
        while left:
            seed = left.pop(0)
            g = {"towns": [seed], "work": t.work[seed], "base": seed, "big": False}
            for j in sorted(left, key=lambda j: dist(t.loc[seed], t.loc[j])):
                if dist(t.loc[seed], t.loc[j]) <= MAX_RADIUS_KM and g["work"] + t.work[j] <= cap:
                    g["towns"].append(j); g["work"] += t.work[j]
            left = [j for j in left if j not in g["towns"]]
            groups.append(g)

    # Join small groups: same county first, then the same province
    changed = True
    while changed:
        changed = False
        for g in sorted([g for g in groups if g["work"] < cap * 0.5], key=lambda g: g["work"]):
            if g not in groups:
                continue
            b = t.loc[g["base"]]
            best = None
            for h in groups:
                if h is g or t.province[h["base"]] != b.province:
                    continue
                hb = t.loc[h["base"]]
                far = max(dist(hb, t.loc[j]) for j in g["towns"])
                fits = h["work"] + g["work"] <= cap or h["big"]   # a big city may grow into one more visitor
                if far <= MAX_RADIUS_KM and fits:
                    score = (hb.county != b.county, far)
                    if best is None or score < best[0]:
                        best = (score, h)
            if best:
                h = best[1]
                h["towns"] += g["towns"]; h["work"] += g["work"]
                groups.remove(g); changed = True

    df["territory"], df["_base"] = "", None
    for g in groups:
        b = t.loc[g["base"]]
        members = t.loc[g["towns"]]
        if g["big"]:
            label = f"شهر {b.city}" + (" و اطراف" if len(members) > 1 else "")
        elif len(members) == 1:
            label = f"شهر {b.city}"
        else:
            label = f"حوزه {b.city} (شهرستان " + "، ".join(dict.fromkeys(members.county)) + ")"
        for _, m in members.iterrows():
            sel = (df.province == m.province) & (df.county == m.county) & (df.city == m.city)
            df.loc[sel, "territory"] = label
            df.loc[sel, "_base"] = pd.Series([(b.province, b.county, b.city)] * sel.sum(),
                                             index=df.index[sel], dtype=object)
    return df


def town_order(g, P, base):
    """Order of the towns of a territory: start at the main town, then the nearest unvisited town."""
    towns = list(dict.fromkeys(g._town))
    order, left = [base], [x for x in towns if x != base]
    while left:
        cur = P[order[-1]]
        d = [haversine_km(cur.lat, cur.lon, P[x].lat, P[x].lon) for x in left]
        d = [x if np.isfinite(x) else 1e6 for x in d]
        order.append(left.pop(int(np.argmin(d))))
    return {x: i for i, x in enumerate(order)}


WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه"]


def plan(df, prof, a):
    budget = a.hours * 60 - a.break_min                 # working minutes per day
    cycle_days = a.days_per_week * a.weeks              # working days per visit cycle
    df = df.copy()
    df["_key"] = hierarchy_key(df)
    df["_town"] = list(zip(df.province, df.county, df.city))
    df["service_min"], df["crowded"] = service_minutes(df, prof)
    P = prof.set_index(["province", "county", "city"])
    P.index = P.index.to_flat_index()
    pt = P.loc[df["_town"]]
    df["_work"] = (df.service_min.values + pt.hop_km.values / pt.speed_kmh.values * 60 + pt.parking_min.values
                   + pt.commute_km.values / pt.speed_kmh.values * 60 / 10)
    df = build_territories(df, cycle_days * budget, prof[["province", "county", "city", "lat", "lon"]])
    start = int(a.start[:2]) * 60 + int(a.start[3:])
    clock_prof = dict(zip(P.index, P.itertuples(index=False)))
    # Phase 1: daily routes of each territory (each day starts from the territory's main town)
    terrs = []
    for (prov, terr), g in df.groupby(["province", "territory"], sort=True):
        base = g._base.iloc[0]                           # the visitors' base: the territory's main town
        rank = town_order(g, clock_prof, base)
        g = (g.assign(_o=g._town.map(rank)).sort_values(["_o", "_key"]).drop(columns="_o")
               .reset_index(drop=True))
        geo = g.lat.notna().mean() >= 0.9
        if geo:
            g[["lat", "lon"]] = g[["lat", "lon"]].fillna(g[["lat", "lon"]].mean())
            # With coordinates, the order within each town follows a Hilbert curve (neighbors stay together)
            g["_h"] = hilbert_index(g.lat.values, g.lon.values)
            g = (g.assign(_o=g._town.map(rank)).sort_values(["_o", "_h"]).drop(columns=["_o", "_h"])
                   .reset_index(drop=True))
        clock = DayClock(P, base, geo)
        days = build_days(g.to_dict("records"), clock, budget)
        if geo:                                          # shortest order inside each day (same town)
            for i, d in enumerate(days):
                if len(d) > 2 and len({r["_town"] for r in d}) == 1:
                    xy = to_xy(np.array([r["lat"] for r in d]), np.array([r["lon"] for r in d]))
                    days[i] = [d[j] for j in tsp_open(xy)]
        terrs.append(dict(prov=prov, terr=terr, base=base, days=days, clock=clock, geo=geo, rank=rank))

    # Phase 2: visitors. A big territory gets its own visitor(s); small territories of one province are
    # chained geographically (nearest main town) and packed into one visitor while the days fit the cycle.
    plans = []                                           # (list of (territory, day))
    for prov in dict.fromkeys(t["prov"] for t in terrs):
        T = [t for t in terrs if t["prov"] == prov]
        for t in [t for t in T if len(t["days"]) >= cycle_days * 0.75]:
            k = math.ceil(len(t["days"]) / cycle_days)   # fewest visitors that cover all days in one cycle
            keys_ = [f"{t['rank'][d[0]['_town']]:03d}{d[0]['_key']}" for d in t["days"]]
            vlab = postal_cuts(keys_, k, cycle_days, win=2)
            for v in range(k):
                plans.append([(t, d) for d, l in zip(t["days"], vlab) if l == v])
        small = sorted([t for t in T if len(t["days"]) < cycle_days * 0.75], key=lambda t: -len(t["days"]))
        chain = small[:1]
        left = small[1:]
        while left:
            c = clock_prof[chain[-1]["base"]]
            dd = [haversine_km(c.lat, c.lon, clock_prof[t["base"]].lat, clock_prof[t["base"]].lon) for t in left]
            dd = [x if np.isfinite(x) else 1e6 for x in dd]
            chain.append(left.pop(int(np.argmin(dd))))
        cur = []
        for t in chain:
            if cur and len(cur) + len(t["days"]) > cycle_days:
                plans.append(cur); cur = []
            cur += [(t, d) for d in t["days"]]
        if cur:
            plans.append(cur)

    rows = []
    for vid, vdays in enumerate(plans, 1):
        n_terr = len({id(t) for t, _ in vdays})
        for dn, (t, d) in enumerate(vdays, 1):
            sch = day_schedule(d, t["clock"], start)
            end = sch[-1]["leave_min"]
            for stop, (r, s_) in enumerate(zip(d, sch), 1):
                r = dict(r)
                r.update(s_, territory=t["terr"], visitor=f"V{vid:04d}", visitor_territories=n_terr, day=dn,
                         week=(dn - 1) // a.days_per_week + 1,
                         weekday=WEEKDAYS[(dn - 1) % a.days_per_week],
                         group=f"V{vid:04d}-روز{dn:02d}", stop=stop, visits_in_day=len(d),
                         arrive=hhmm(s_["arrive_min"]), leave=hhmm(s_["leave_min"]), day_end=hhmm(end),
                         day_work_min=round(end - start), base_town=t["base"][2],
                         mode="geographic" if t["geo"] else "postal code + neighborhood")
                rows.append(r)
    out = pd.DataFrame(rows)
    keys = ["province", "county", "city"]
    return out.merge(prof[keys + ["population", "population_estimated", "city_class", "speed_kmh"]],
                     on=keys, how="left")


# ---------------------------------------------------------------- output
FA = {
    "province": "استان", "county": "شهرستان", "city": "شهر", "neighborhood": "محله/ناحیه",
    "population": "جمعیت شهر", "city_class": "اندازه شهر", "territory": "منطقه/قلمرو",
    "visitor": "کد ویزیتور", "visitor_territories": "تعداد حوزه‌های ویزیتور", "base_town": "شهر مبدا روز",
    "week": "هفته", "weekday": "روز هفته", "day": "روز کاری", "group": "گروه (ویزیتور-روز)",
    "stop": "ترتیب ویزیت", "arrive": "ساعت رسیدن", "leave": "ساعت خروج", "travel_min": "زمان رفت (دقیقه)",
    "travel_km": "مسافت رفت (کیلومتر)", "service_min": "زمان داخل داروخانه (دقیقه)",
    "crowded": "منطقه شلوغ", "visits_in_day": "تعداد ویزیت روز", "day_end": "پایان کار روز",
    "gln": "کد جی ال ان", "name": "نام مرکز", "category": "نوع مرکز", "owner": "مالک/رابط",
    "postal": "کد پستی", "address": "آدرس", "lat": "عرض جغرافیایی", "lon": "طول جغرافیایی",
    "coord_source": "منبع مختصات", "mode": "روش مسیریابی", "city_raw": "شهر (اصلی فایل)",
    "city_method": "روش تعیین شهر", "nbh_method": "روش تعیین محله", "flags": "هشدارهای پاکسازی",
    "source_file": "فایل منبع",
    "customers": "تعداد مشتری", "visitors": "تعداد ویزیتور", "groups": "تعداد گروه",
    "counties": "شهرستان‌ها", "cities": "شهرها", "days": "تعداد روز کاری",
    "visits_per_day": "میانگین ویزیت در روز", "km_per_day": "میانگین مسافت روز (کیلومتر)",
    "travel_min_per_day": "میانگین زمان رانندگی روز (دقیقه)",
    "service_min_per_day": "میانگین زمان داخل داروخانه روز (دقیقه)",
    "work_min_per_day": "میانگین کل زمان کار روز (دقیقه)", "utilization_%": "درصد ظرفیت (روزها)",
    "avg_service_min": "میانگین زمان ویزیت (دقیقه)", "avg_travel_min": "میانگین زمان رفت (دقیقه)",
    "speed_kmh": "سرعت متوسط ترافیک (km/h)", "area_km2": "مساحت تخمینی (km²)",
    "hop_km": "فاصله تخمینی بین دو داروخانه (km)", "records": "تعداد رکورد",
    "population_estimated": "جمعیت تخمینی؟",
}


def write(p, excluded, prof, path, a):
    cols = ["province", "county", "city", "population", "city_class", "neighborhood", "territory", "visitor",
            "visitor_territories", "base_town", "week", "weekday", "day", "group", "stop", "arrive", "leave",
            "travel_min", "travel_km", "service_min", "crowded", "visits_in_day", "day_end", "gln", "name",
            "category", "owner", "postal", "address", "lat", "lon", "coord_source", "mode", "city_raw",
            "city_method", "nbh_method", "flags", "source_file"]
    routes = p[cols].sort_values(["province", "county", "city", "visitor", "day", "stop"])
    days = (p.groupby(["visitor", "day"])
            .agg(visits=("gln", "size"), km=("travel_km", "sum"), travel=("travel_min", "sum"),
                 service=("service_min", "sum"), work=("day_work_min", "first"))
            .reset_index())
    per_v = (days.groupby("visitor")
             .agg(visits_per_day=("visits", "mean"), km_per_day=("km", "mean"),
                  travel_min_per_day=("travel", "mean"), service_min_per_day=("service", "mean"),
                  work_min_per_day=("work", "mean"))
             .round(1).reset_index())
    vis = (p.groupby(["province", "visitor"])
           .agg(territory=("territory", lambda s: " | ".join(dict.fromkeys(s))), counties=("county", lambda s: "، ".join(dict.fromkeys(s))),
                cities=("city", lambda s: "، ".join(dict.fromkeys(s))),
                city_class=("city_class", lambda s: s.mode().iloc[0]), customers=("gln", "size"),
                days=("day", "max"))
           .reset_index().merge(per_v, on="visitor"))
    vis["utilization_%"] = (vis.days / (a.days_per_week * a.weeks) * 100).round(0)
    keys = ["province", "county", "city"]
    vpd = (p.groupby(keys + ["visitor", "day"]).size().groupby(keys).mean()
           .round(1).rename("visits_per_day").reset_index())
    city = (p.groupby(keys + ["population", "city_class"])
            .agg(customers=("gln", "size"), visitors=("visitor", "nunique"), territory=("territory", "first"),
                 avg_service_min=("service_min", "mean"), avg_travel_min=("travel_min", "mean"))
            .round(1).reset_index().merge(vpd, on=keys)
            .sort_values(["province", "county", "customers"], ascending=[True, True, False]))
    order = {c[1]: i for i, c in enumerate(CLASSES)}
    cls = (vis.groupby("city_class")
           .agg(visitors=("visitor", "size"), customers=("customers", "sum"),
                visits_per_day=("visits_per_day", "mean"), km_per_day=("km_per_day", "mean"),
                travel_min_per_day=("travel_min_per_day", "mean"),
                service_min_per_day=("service_min_per_day", "mean"), work_min_per_day=("work_min_per_day", "mean"))
           .round(1).reset_index().sort_values("city_class", key=lambda s: s.map(order)))
    nbh = (p.groupby(keys + ["neighborhood"])
           .agg(customers=("gln", "size"), visitors=("visitor", lambda s: "، ".join(sorted(set(s)))),
                groups=("group", "nunique"))
           .reset_index())
    params = prof[keys + ["population", "population_estimated", "city_class", "speed_kmh", "area_km2",
                          "hop_km", "records"]].round(2)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for df_, name in [(routes, "برنامه ویزیت"), (cls, "مقایسه اندازه شهرها"), (vis, "خلاصه ویزیتورها"),
                          (city, "خلاصه شهرها"), (nbh, "استان-شهرستان-شهر-محله"), (params, "پارامترهای شهرها"),
                          (excluded, "خارج از برنامه")]:
            if len(df_):
                df_.rename(columns=FA).to_excel(xw, sheet_name=name, index=False)
        for ws in xw.book.worksheets:
            ws.sheet_view.rightToLeft = True
            ws.freeze_panes = "A2"
            for col in ws.columns:
                w = max(len(str(c.value or "")) for c in list(col)[:300])
                ws.column_dimensions[col[0].column_letter].width = min(60, max(8, w + 2))
    return vis, cls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=9, help="hours at work per day")
    ap.add_argument("--break-min", type=float, default=30, help="lunch/prayer break per day (minutes)")
    ap.add_argument("--days-per-week", type=int, default=5)
    ap.add_argument("--weeks", type=int, default=4, help="length of the visit cycle (each customer once)")
    ap.add_argument("--start", default="08:00", help="start time of the working day")
    ap.add_argument("--geocode-file", default=str(WORK / "geocode.csv"))
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    df = pd.read_pickle(WORK / "clean.pkl")
    pop = pd.read_csv(ROOT / "data" / "city_population.csv")
    dups = df[df.is_duplicate].assign(reason="duplicate")
    df = attach_coords(df[~df.is_duplicate].copy(), Path(a.geocode_file))
    print("coordinates:", df.coord_source.replace("", "none").value_counts().to_dict())

    for tag, keep in [("pharmacies_only", df.is_pharmacy), ("all_centers", df.is_pharmacy | True)]:
        excluded = pd.concat([df[~keep].assign(reason="not a pharmacy: " + df.category), dups])
        prof = city_profiles(df[keep], pop)
        p = plan(df[keep], prof, a)
        vis, cls = write(p, excluded, prof, OUT / f"visit_plan_{tag}.xlsx", a)
        print(f"\n== {tag}: {len(p)} customers, {vis.visitor.nunique()} visitors")
        print(cls.to_string(index=False))


if __name__ == "__main__":
    main()
