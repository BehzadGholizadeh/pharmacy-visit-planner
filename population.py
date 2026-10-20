"""
City population and coordinates from Wikidata (census populations of cities and villages in Iran),
matched to the (province, county, city) values of the cleaned data.

    python population.py            # uses data/wikidata_settlements_raw.csv if it exists, otherwise downloads it
Output: data/city_population.csv
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from clean import norm, norm_key

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "wikidata_settlements_raw.csv"
OUT = ROOT / "data" / "city_population.csv"

SPARQL = """
SELECT ?item ?fa ?pop ?popdate ?coord ?cls ?prov ?county WHERE {
  VALUES ?cls { wd:Q56557504 wd:Q1549591 wd:Q515 wd:Q532 }
  ?item wdt:P17 wd:Q794; wdt:P31 ?cls; p:P1082 ?ps. ?ps ps:P1082 ?pop.
  OPTIONAL { ?ps pq:P585 ?popdate. }
  OPTIONAL { ?item wdt:P625 ?coord. }
  OPTIONAL { ?item wdt:P131+ ?c. ?c wdt:P31 wd:Q137535. ?c rdfs:label ?county FILTER(lang(?county)='fa') }
  OPTIONAL { ?item wdt:P131+ ?p. ?p wdt:P31 wd:Q1344695. ?p rdfs:label ?prov FILTER(lang(?prov)='fa') }
  ?item rdfs:label ?fa FILTER(lang(?fa)='fa')
}"""


def download():
    r = requests.get("https://query.wikidata.org/sparql", params={"query": SPARQL, "format": "json"},
                     headers={"User-Agent": "pharmacy-planner/1.0"}, timeout=300)
    r.raise_for_status()
    rows = [{k: v["value"] for k, v in x.items()} for x in r.json()["results"]["bindings"]]
    RAW.parent.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(RAW, index=False)


def settlements():
    w = pd.read_csv(RAW, dtype=str)
    w["pop"] = pd.to_numeric(w["pop"], errors="coerce")
    w["is_city"] = ~w["cls"].str.endswith("Q532")
    # The latest population of each item (2016 census over 2006); an item may sit under several
    # provinces/counties (historical divisions), so every (province, county) pair is kept for matching
    latest = (w.sort_values(["item", "popdate"], na_position="first")
                .groupby("item")[["pop", "popdate", "coord", "fa", "is_city"]].last())
    xy = latest["coord"].str.extract(r"Point\(([-\d.]+) ([-\d.]+)\)").astype(float)
    latest["lon"], latest["lat"] = xy[0], xy[1]
    adm = w[["item", "prov", "county"]].drop_duplicates()
    w = adm.join(latest, on="item")
    w["name"] = w["fa"].map(lambda s: norm(re.sub(r"\s*\(.*?\)", "", s)))
    w["province"] = w["prov"].fillna("").map(lambda s: norm(s.replace("استان", "")))
    w["county"] = w["county"].fillna("").map(lambda s: norm(s.replace("شهرستان", "")))
    w["k"] = w["name"].map(norm_key)
    return w[["item", "k", "name", "province", "county", "pop", "lat", "lon", "is_city", "popdate"]]


def main():
    if not RAW.exists():
        download()
    w = settlements()
    df = pd.read_pickle(ROOT / "work" / "clean.pkl")
    cities = df.groupby(["province", "county", "city"]).size().rename("records").reset_index()
    pk = lambda s: norm_key(s)
    w["pk"], w["ck"] = w.province.map(pk), w.county.map(pk)
    out = []
    strip = lambda k: re.sub(r"^(بندر|شهر)", "", k)
    w["k2"] = w.k.map(strip)
    for r in cities.itertuples(index=False):
        ck = norm_key(r.city)
        c = w[w.k == ck]
        c2 = w[(w.k2 == strip(ck)) & w.is_city]                        # «بوشهر» = «بندر بوشهر»
        c3 = w[w.is_city & (w.pk == pk(r.province))
               & w.k.str.startswith(ck)]                                  # «پیران» = «پیرانشهر»
        best, how = None, "not found"
        for cand, cond, label in [(c, (c.pk == pk(r.province)) & (c.ck == pk(r.county)), "name+province+county"),
                                  (c, c.pk == pk(r.province), "name+province"),
                                  (c, c.ck == pk(r.county), "name+county"),
                                  (c2, c2.pk == pk(r.province), "name variant (بندر/شهر)+province"),
                                  (c3, c3.ck == pk(r.county), "partial name+county")]:
            m = cand[cond]
            if len(m):
                # City before village; then the largest population
                best = m.sort_values(["is_city", "pop"], ascending=False).iloc[0]; how = label; break
        out.append({**r._asdict(),
                    "population": best["pop"] if best is not None else np.nan,
                    "lat": best["lat"] if best is not None else np.nan,
                    "lon": best["lon"] if best is not None else np.nan,
                    "settlement_type": ("city" if best["is_city"] else "village") if best is not None else "",
                    "census_date": str(best["popdate"])[:4] if best is not None else "",
                    "match": how})
    out = pd.DataFrame(out)
    # Unmatched: the county center (the most populous matched city in the same county)
    for i in out.index[out.match == "not found"]:
        r = out.loc[i]
        same = out[(out.province == r.province) & (out.county == r.county) & out.lat.notna()]
        if len(same):
            s = same.sort_values("population", ascending=False).iloc[0]
            out.loc[i, ["lat", "lon"]] = s[["lat", "lon"]].values
            out.loc[i, "match"] = "coordinates = county center; population unknown"
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    rec = out.groupby(out.match)["records"].sum()
    print(out.match.value_counts().to_string()); print("records by match:\n" + rec.to_string())
    print(out.sort_values("records", ascending=False).head(12).to_string(index=False))


if __name__ == "__main__":
    main()
