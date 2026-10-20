"""
Step 2: cluster each city into visitor territories and daily routes, and order the visits.

    python plan_routes.py                        # both versions (pharmacies only / all centers)
    python plan_routes.py --per-day 8 --days 22  # visitor capacity

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


def build_territories(df, cap):
    """Territory = a big city on its own; small cities are grouped within their own county; leftover
    small cities in a county with a big city join that city ("و اطراف"); still-small groups are joined
    with neighboring counties in the same province."""
    df["territory"] = ""
    tkey = {}                                            # territory -> its first key (for proximity)
    sizes = df.groupby(["province", "county", "city"]).size()
    for (p, c, t), n in sizes.items():
        if n >= cap * 0.75:
            m = (df.province == p) & (df.county == c) & (df.city == t)
            df.loc[m, "territory"] = f"شهر {t}"
    for p, gp in df[df.territory == ""].groupby("province"):
        groups = []                                      # [counties, mask, size, key]
        for c, gc in gp.groupby("county"):
            cities = gc.groupby("city")["_key"].agg(["min", "size"]).sort_values("min")
            for grp in pack(list(zip(cities.index, cities["size"])), cap):
                m = (df.province == p) & (df.county == c) & df.city.isin(grp) & (df.territory == "")
                n = int(m.sum())
                big = df[(df.province == p) & (df.county == c) & (df.territory != "")]
                if n < cap * 0.5 and len(big):
                    # Attach to the smallest big-city territory of the same county
                    host = big.territory.value_counts().index[-1]
                    df.loc[df.province.eq(p) & df.territory.eq(host), "territory"] = host + " و اطراف"
                    df.loc[m, "territory"] = host + " و اطراف" if not host.endswith("و اطراف") else host
                    continue
                groups.append(([c], m, n, cities.loc[grp, "min"].min()))
        groups.sort(key=lambda x: x[3])
        units = [(i, g[2] if g[2] < cap * 0.5 else cap) for i, g in enumerate(groups)]
        packed = pack(units, cap)
        # A group that is still very small (< 25% of capacity) joins its neighbor in province order
        i = 0
        while i < len(packed):
            if len(packed) > 1 and sum(groups[j][2] for j in packed[i]) < cap * 0.25:
                nb = i - 1 if i > 0 else i + 1
                packed[nb] = sorted(packed[nb] + packed[i]); packed.pop(i)
                i = max(0, i - 1)
            else:
                i += 1
        for grp in packed:
            label = "شهرستان " + "، ".join(dict.fromkeys(c for j in grp for c in groups[j][0]))
            for j in grp:
                df.loc[groups[j][1], "territory"] = label
    return df


def plan(df, per_day, days):
    cap = per_day * days
    df = df.copy()
    df["_key"] = hierarchy_key(df)
    df = build_territories(df, cap)
    rows = []
    vid = 0
    for (prov, terr), g in df.groupby(["province", "territory"], sort=True):
        g = g.sort_values("_key").reset_index(drop=True)
        n = len(g)
        k = math.ceil(n / cap)                         # minimum visitor count without exceeding capacity
        per_v = math.ceil(n / k)
        # Geographic mode if at least 90% of the points have coordinates; the rest get the territory center
        geo = g.lat.notna().mean() >= 0.9
        if geo:
            g[["lat", "lon"]] = g[["lat", "lon"]].fillna(g[["lat", "lon"]].mean())
            xy = to_xy(g.lat.values, g.lon.values)
            vlab = balanced_kmeans(xy, k, per_v)
            # Number the visitors in the hierarchy order (the first member of each cluster)
            first = [g._key[vlab == v].min() for v in range(k)]
            vlab = np.argsort(np.argsort(first))[vlab]
        else:
            vlab = postal_cuts(g._key.tolist(), k, per_v)
        for v in range(k):
            vid += 1
            sub = g[vlab == v].sort_values("_key").reset_index(drop=True)
            m = len(sub)
            d = min(days, math.ceil(m / per_day))
            if geo:
                sxy = to_xy(sub.lat.values, sub.lon.values)
                dlab = balanced_kmeans(sxy, d, math.ceil(m / d), seed=v)
                dc = np.array([sxy[dlab == j].mean(0) for j in range(d)])
                day_order = tsp_open(dc)                 # order of days: consecutive days stay in adjacent areas
            else:
                dlab = postal_cuts(sub._key.tolist(), d, per_day, win=3)
                day_order = list(range(d))
            for day_no, j in enumerate(day_order, 1):
                idx = np.flatnonzero(dlab == j)
                if geo:
                    order = [idx[i] for i in tsp_open(sxy[idx])]
                    km = path_len(sxy, order) * ROAD_FACTOR
                else:
                    order = sorted(idx, key=lambda i: sub._key[i])
                    km = np.nan
                for stop, i in enumerate(order, 1):
                    r = sub.loc[i].to_dict()
                    r.update(visitor=f"V{vid:04d}", visitor_in_territory=v + 1, day=day_no,
                             group=f"V{vid:04d}-روز{day_no:02d}", stop=stop,
                             day_km=round(km, 1) if stop == 1 and geo else np.nan,
                             mode="geographic" if geo else "postal code + neighborhood")
                    rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- output
FA = {
    "province": "استان", "county": "شهرستان", "city": "شهر", "neighborhood": "محله/ناحیه",
    "group": "گروه (ویزیتور-روز)", "coord_source": "منبع مختصات", "nbh_method": "روش تعیین محله", "territory": "منطقه/قلمرو", "visitor": "کد ویزیتور",
    "visitor_in_territory": "ویزیتور شماره (در قلمرو)", "day": "روز", "stop": "ترتیب ویزیت",
    "gln": "کد جی ال ان", "name": "نام مرکز", "category": "نوع مرکز", "owner": "مالک/رابط",
    "postal": "کد پستی", "address": "آدرس", "lat": "عرض جغرافیایی", "lon": "طول جغرافیایی",
    "day_km": "مسافت تقریبی روز (کیلومتر)", "mode": "روش مسیریابی", "city_raw": "شهر (اصلی فایل)",
    "city_method": "روش تعیین شهر", "flags": "هشدارهای پاکسازی", "source_file": "فایل منبع",
}


def write(plan_df, excluded, path, per_day, days):
    cols = ["province", "county", "city", "neighborhood", "territory", "visitor", "visitor_in_territory",
            "day", "group", "stop", "gln", "name", "category", "owner", "postal", "address", "lat", "lon",
            "coord_source", "day_km", "mode", "city_raw", "city_method", "nbh_method", "flags", "source_file"]
    routes = plan_df[cols].sort_values(["province", "county", "city", "visitor", "day", "stop"])
    vis = (plan_df.groupby(["province", "territory", "visitor"])
           .agg(counties=("county", lambda s: "، ".join(dict.fromkeys(s))),
                cities=("city", lambda s: "، ".join(dict.fromkeys(s))), customers=("gln", "size"),
                days=("day", "max"), km_total=("day_km", lambda s: s.sum(min_count=1)))
           .reset_index())
    vis["utilization_%"] = (vis.customers / (per_day * days) * 100).round(0)
    city = (plan_df.groupby(["province", "county", "city"])
            .agg(customers=("gln", "size"), visitors=("visitor", "nunique"), territory=("territory", "first"))
            .reset_index().sort_values(["province", "county", "customers"], ascending=[True, True, False]))
    nbh = (plan_df.groupby(["province", "county", "city", "neighborhood"])
           .agg(customers=("gln", "size"), visitors=("visitor", lambda s: "، ".join(sorted(set(s)))),
                groups=("group", "nunique"))
           .reset_index())
    city["customers_per_visitor"] = (city.customers / city.visitors).round(0)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        routes.rename(columns=FA).to_excel(xw, sheet_name="برنامه ویزیت", index=False)
        nbh.rename(columns={**FA, "customers": "تعداد مشتری", "visitors": "ویزیتورها", "groups": "تعداد گروه"}
                   ).to_excel(xw, sheet_name="استان-شهرستان-شهر-محله", index=False)
        vis.rename(columns={**FA, "counties": "شهرستان‌ها", "cities": "شهرها", "customers": "تعداد مشتری", "days": "تعداد روز",
                            "km_total": "مسافت کل تقریبی (کیلومتر)", "utilization_%": "درصد ظرفیت"}
                   ).to_excel(xw, sheet_name="خلاصه ویزیتورها", index=False)
        city.rename(columns={**FA, "customers": "تعداد مشتری", "visitors": "تعداد ویزیتور",
                             "customers_per_visitor": "مشتری به ازای هر ویزیتور"}
                    ).to_excel(xw, sheet_name="خلاصه شهرها", index=False)
        if len(excluded):
            excluded.rename(columns=FA).to_excel(xw, sheet_name="خارج از برنامه", index=False)
        for ws in xw.book.worksheets:
            ws.sheet_view.rightToLeft = True
            ws.freeze_panes = "A2"
            for col in ws.columns:
                w = max(len(str(c.value or "")) for c in list(col)[:300])
                ws.column_dimensions[col[0].column_letter].width = min(60, max(8, w + 2))
    return vis, city


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-day", type=int, default=8)
    ap.add_argument("--days", type=int, default=22)
    ap.add_argument("--geocode-file", default=str(WORK / "geocode.csv"))
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    df = pd.read_pickle(WORK / "clean.pkl")
    dups = df[df.is_duplicate].assign(reason="duplicate")
    df = attach_coords(df[~df.is_duplicate].copy(), Path(a.geocode_file))
    print("coordinates:", df.coord_source.replace("", "none").value_counts().to_dict())

    for tag, keep in [("pharmacies_only", df.is_pharmacy), ("all_centers", df.is_pharmacy | True)]:
        excluded = pd.concat([df[~keep].assign(reason="not a pharmacy: " + df.category), dups])
        p = plan(df[keep], a.per_day, a.days)
        vis, city = write(p, excluded, OUT / f"visit_plan_{tag}.xlsx", a.per_day, a.days)
        print(f"\n== {tag}: {len(p)} customers, {vis.visitor.nunique()} visitors, "
              f"average utilization {vis['utilization_%'].mean():.0f}%")
        print(city.sort_values("customers", ascending=False).head(8).to_string(index=False))


if __name__ == "__main__":
    main()
