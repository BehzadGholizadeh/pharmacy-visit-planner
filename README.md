# Pharmacy Visit Planner

Cleans the Iranian pharmacy customer lists (`Customers_*.xlsx`), divides them into visitor zones by province → county → city → neighborhood, and builds each visitor's daily schedule on a time budget (visit time + travel + traffic).

## Python Pipeline (existing)

```bash
python clean.py                                   # cleaning -> output/cleaned_data.xlsx
python population.py                              # city population and coordinates (Wikidata) -> data/city_population.csv
python geocode_neshan.py                          # optional: pharmacy coordinates from Neshan (needs NESHAN_API_KEY)
python plan_routes.py --hours 9 --days-per-week 5 --weeks 4
```

See `timing.py` for the full time model.

## Android Driver App (new)

A native Android application for the drivers/visitors who execute the daily routes.

### Location
```
android/
```

### Documentation & Phased Plan
- **Product Requirements**: [`docs/product/driver-module-prd.md`](docs/product/driver-module-prd.md)
- **Phase 1 (MVP)**: [`docs/phases/phase-01-mvp.md`](docs/phases/phase-01-mvp.md) ← **Start here**
- Phase 2 & 3 are also documented in the same folder.

### How to continue development with Gemini
1. Open the `android/` folder in Android Studio.
2. Copy the prompt from `docs/phases/phase-01-mvp.md` into Gemini.
3. Work phase by phase. Always instruct Gemini to make the smallest possible changes.

### Current Status (2026-10-30)
- ✅ Repository structure created
- ✅ Basic Android scaffold (Compose + Hilt + Navigation + sample UI)
- ✅ Login screen + Today’s Route screen with fake data
- ⏳ Full Room + Domain layer + Stop Detail + real navigation → Phase 1 remaining tasks

## Requirements
- Python 3.9+ (pandas, numpy, scikit-learn, openpyxl, requests)
- Android Studio Ladybug or newer (for the driver app)
