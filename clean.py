"""
Step 1: read every Customers_*.xlsx file, clean and normalize the data.

Output: work/clean.parquet (or .pkl) plus a cleaning report.
    python clean.py
"""
import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)

COLS = {
    "کد جی ال ان": "gln",
    "کد Hix": "hix",
    "نام داروخانه": "name",
    "کد پستی": "postal",
    "نام مالک/ رابط مرکز": "owner",
    "استان": "province_raw",
    "شهرستان": "county_raw",
    "شهر": "city_raw",
    "آدرس": "address",
}

_TRANS = str.maketrans({
    "ي": "ی", "ى": "ی", "ئ": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "أ": "ا", "إ": "ا", "ؤ": "و",
    "‌": " ", "‏": " ", "‎": " ", "\xa0": " ", "ـ": "",
    **{chr(0x06F0 + i): str(i) for i in range(10)},   # Persian digits
    **{chr(0x0660 + i): str(i) for i in range(10)},   # Arabic digits
})
_DIACRITICS = re.compile(r"[ً-ْٰ]")


def norm(s):
    if pd.isna(s):
        return ""
    s = _DIACRITICS.sub("", str(s).translate(_TRANS))
    return re.sub(r"\s+", " ", s).strip()


def norm_key(s):
    """Key for comparing names: drop spaces and «آ» variants."""
    return norm(s).replace("آ", "ا").replace(" ", "")


# ---------- center type ----------
CATEGORY_RULES = [
    ("داروخانه", r"داروخانه|دارو خانه|فارمسی|pharm"),
    ("دندانپزشکی", r"دندان|ارتودنس|ارتودنسی|پروتز"),
    ("بیمارستان", r"بیمارستان"),
    ("آزمایشگاه", r"آزمایشگاه|ازمایشگاه|پاتوبیولوژی|رادیولوژی|سونوگرافی|تصویربرداری"),
    ("درمانگاه/کلینیک", r"درمانگاه|کلینیک|پلی ?کلینیک|مرکز|همودیالیز|دیالیز|بهداشت|خانه بهداشت|پایگاه|ارتش|سپاه|تامین اجتماعی"),
    ("مطب", r"مطب"),
]


STREET_LIKE = {
    "مرکزی", "حومه", "منطقه", "شریعتی", "گلستان", "قدس", "کشاورز", "سعادت آباد", "جنت آباد",
    "طالقان", "نور", "ارم", "فردوس", "دانش", "آستانه", "ویس", "اسلام آباد", "علی اباد", "علی آباد",
    "شهریار", "آزادی", "امام", "بهار", "صفا", "نصر", "انقلاب", "فرهنگ", "امیریه", "ولیعصر",
    "بهشتی", "مطهری", "پاسداران", "فرودگاه", "صادقیه", "نیاوران", "شهرک", "بازار",
}

# Neighborhoods/districts that belong to the Tehran metropolitan area for routing purposes
METRO_MERGE = {"تجریش": "تهران", "شمیرانات": "تهران", "شمیران": "تهران"}


_NBH_STOP = (r"(?:خیابان|خ |کوچه|بلوار|میدان|بزرگراه|اتوبان|جاده|پلاک|بن ?بست|نبش|طبقه|بلوک|"
             r"ساختمان|مجتمع|روبروی|جنب|بعد|قبل|،|,|-)")
_NBH_RX = re.compile(r"منطقه\s+(.+?)\s*" + _NBH_STOP)


def extract_neighborhoods(df):
    """Neighborhood of each address:
    1) from the standard Post (GNAF) address format: «... منطقه <neighborhood> خیابان ...»
    2) a vote over records with the same postal-code prefix (7, 6 or 5 digits) in the same city
    3) a known neighborhood name of that city as a whole word in the address
    4) otherwise: postal area (first 5 digits)"""
    nbh = df["address"].map(lambda a: (m.group(1).strip() if (m := _NBH_RX.search(a + " ،")) else None))
    nbh = nbh.where(nbh.str.len().between(2, 40))
    method = pd.Series(np.where(nbh.notna(), "address", ""), index=df.index)
    t = df[nbh.notna() & df.postal_valid].assign(nbh=nbh)
    for k in (7, 6, 5):
        m = nbh.isna() & df.postal_valid
        vc = (t.groupby(["city", t.postal.str[:k]]).nbh
                .agg(lambda s: s.value_counts().index[0] if s.value_counts(normalize=True).iloc[0] >= 0.6 else None)
                .dropna())
        key = pd.MultiIndex.from_arrays([df.loc[m, "city"], df.loc[m, "postal"].str[:k]])
        hit = pd.Series(vc.reindex(key).values, index=df.index[m]).dropna()
        nbh[hit.index] = hit
        method[hit.index] = f"postal ({k} digits)"
    known = t.groupby("city").nbh.agg(lambda s: sorted({x for x in s if len(x) >= 4}, key=len, reverse=True))
    for i in df.index[nbh.isna()]:
        a = df.at[i, "address"]
        for x in known.get(df.at[i, "city"], []):
            if re.search(rf"(?:^|[\s،,.\-/]){re.escape(x)}(?=$|[\s،,.\-/])", a):
                nbh[i] = x; method[i] = "name in address"; break
    rest = nbh.isna()
    nbh[rest] = np.where(df.loc[rest, "postal_valid"], "postal area " + df.loc[rest, "postal"].str[:5], "unknown")
    method[rest] = "postal area"
    return nbh, method


def categorize(name):
    for cat, pat in CATEGORY_RULES:
        if re.search(pat, name, flags=re.I):
            return cat
    return "داروخانه"   # by default «دکتر X» / a person's name = pharmacy


def main():
    files = sorted(glob.glob(str(ROOT / "Customers_*.xlsx")))
    raw = pd.concat(
        [pd.read_excel(f, dtype=str).assign(source_file=Path(f).name) for f in files],
        ignore_index=True,
    ).rename(columns=COLS)
    log = {"raw_rows": len(raw)}
    df = raw.copy()

    for c in ["name", "owner", "province_raw", "county_raw", "city_raw", "address"]:
        df[c] = df[c].map(norm)
    df["gln"] = df["gln"].str.strip()
    df = df.drop(columns=["hix"])           # completely empty column

    flags = [[] for _ in range(len(df))]

    def flag(mask, text):
        for i in np.flatnonzero(mask.values):
            flags[i].append(text)

    # ---- name ----
    bad_name = df["name"].str.fullmatch(r"-?\d+|") | (df["name"].str.len() < 2)
    flag(bad_name, "invalid name -> replaced with owner name")
    df.loc[bad_name, "name"] = df.loc[bad_name, "owner"]

    # ---- postal code ----
    df["postal"] = df["postal"].map(norm).str.replace(r"\D", "", regex=True)
    # 10 digits, not starting with 0, and not a placeholder code (1234567890, 1111111111, ...)
    df["postal_valid"] = (df["postal"].str.fullmatch(r"[1-9]\d{9}")
                          & ~df["postal"].map(lambda p: bool(re.search(r"(\d)\1{5}|123456|987654", p))))
    flag(~df["postal_valid"], "invalid postal code")
    log["invalid_postal"] = int((~df["postal_valid"]).sum())

    # ---- center type ----
    df["category"] = df["name"].map(categorize)
    df["is_pharmacy"] = df["category"].eq("داروخانه")

    # ---- fix province / city ----
    # Trusted rows: the city name appears in the address itself.
    addr_key = df["address"].map(norm_key)
    city_key = df["city_raw"].map(norm_key)
    trusted = np.array([len(c) >= 2 and c in a for c, a in zip(city_key, addr_key)])
    log["trusted_city_rows"] = int(trusted.sum())

    # (city, province) gazetteer from the trusted rows
    t = df[trusted]
    city_prov = (t.groupby("city_raw")["province_raw"]
                   .agg(lambda s: s.value_counts().index[0]).to_dict())
    # Add every city name in the file (for cities with no trusted row)
    for c, p in df.groupby("city_raw")["province_raw"].agg(lambda s: s.value_counts().index[0]).items():
        city_prov.setdefault(c, p)
    # Fix the spelling variants of the provinces
    prov_fix = {norm(p): norm(p) for p in df["province_raw"].unique()}
    # Names that are usually a street/neighborhood name or a common phrase in addresses
    provinces = set(prov_fix) - set(t["city_raw"])   # a province name is not a city (unless it is also a city name)
    gaz = sorted((c for c in city_prov if len(c) >= 3 and c not in STREET_LIKE | provinces),
                 key=lambda c: -len(c))
    gaz_re = [(c, re.compile(rf"(?:^|[\s،,.\-/()])(شهر\s+)?{re.escape(c)}(?=$|[\s،,.\-/()])"))
              for c in gaz]

    # postal prefix -> city vote (from the trusted rows)
    vote = {}
    for k in (5, 4, 3):
        g = t[t["postal_valid"]].groupby(t["postal"].str[:k])["city_raw"]
        vc = g.agg(lambda s: (s.value_counts().index[0], s.value_counts(normalize=True).iloc[0], len(s)))
        vote[k] = {p: v for p, v in vc.items() if v[1] >= 0.6 and v[2] >= 2}

    city, method = [], []
    for i, r in enumerate(df.itertuples(index=False)):
        if trusted[i]:
            city.append(r.city_raw); method.append("label confirmed by address"); continue
        # 1) the postal code (most accurate)
        got = None
        if r.postal_valid:
            for k in (5, 4):
                v = vote[k].get(r.postal[:k])
                if v:
                    got = (v[0], f"postal code ({k} digits)"); break
        # 2) a city name inside the address, as a whole word. Accepted only when it
        #    follows «شهر» or belongs to the same province (longest name takes priority).
        if got is None:
            a = r.address
            for c, rx in gaz_re:
                m = rx.search(a)
                if m and (m.group(1) or city_prov.get(c) == r.province_raw):
                    got = (c, "city name in address"); break
        if got is None and r.postal_valid:
            v = vote[3].get(r.postal[:3])
            if v:
                got = (v[0], "postal code (3 digits)")
        if got is None:
            got = (r.city_raw, "original label (not confirmed)")
        city.append(got[0]); method.append(got[1])

    # Spelling variants of one city (باقر شهر / باقرشهر) -> the most common spelling
    ck = pd.Series(city).map(norm_key)
    canon = pd.Series(city).groupby(ck).agg(lambda s: s.value_counts().index[0])
    city = ck.map(canon).tolist()
    df["city"] = [METRO_MERGE.get(c, c) for c in city]
    df["city_method"] = method
    df["province"] = [prov_fix.get(city_prov.get(c, p), p) for c, p in zip(df["city"], df["province_raw"])]
    # County: the most common county of each city (from the trusted rows)
    ref = df[trusted]
    city_county = ref.groupby(["province", "city"])["county_raw"].agg(lambda s: s.value_counts().index[0])
    key = pd.MultiIndex.from_frame(df[["province", "city"]])
    df["county"] = pd.Series(city_county.reindex(key).values, index=df.index).fillna(df["county_raw"])
    df.loc[df["city"].eq("تهران"), "county"] = "تهران"

    changed = df["city"].ne(df["city_raw"])
    flag(changed, "city corrected")
    flag(df["province"].ne(df["province_raw"]), "province corrected")
    flag(df["county"].ne(df["county_raw"]), "county corrected")
    log["county_changed"] = int(df["county"].ne(df["county_raw"]).sum())

    df["neighborhood"], df["nbh_method"] = extract_neighborhoods(df)
    log["city_changed"] = int(changed.sum())
    log["city_unconfirmed"] = int(df["city_method"].str.startswith("original label").sum())

    # ---- duplicates: same postal code + same name ----
    dkey = df["postal"] + "|" + df["name"].map(norm_key)
    dup = dkey.duplicated(keep="first") & df["postal_valid"]
    flag(dup, "duplicate (same postal code and name)")
    df["is_duplicate"] = dup
    log["duplicates"] = int(dup.sum())

    df["flags"] = ["; ".join(f) for f in flags]
    df.to_pickle(WORK / "clean.pkl")
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    with pd.ExcelWriter(out / "cleaned_data.xlsx", engine="openpyxl") as xw:
        df.drop(columns=["postal_valid"]).to_excel(xw, sheet_name="cleaned data", index=False)
        pd.Series(log).rename("value").to_frame().to_excel(xw, sheet_name="cleaning report")
        for ws in xw.book.worksheets:
            ws.sheet_view.rightToLeft = True

    log["pharmacies"] = int((df.is_pharmacy & ~df.is_duplicate).sum())
    log["non_pharmacy"] = int((~df.is_pharmacy & ~df.is_duplicate).sum())
    print(pd.Series(log).to_string())
    print(df["category"].value_counts().to_string())
    print(df["city_method"].value_counts().to_string())


if __name__ == "__main__":
    main()
