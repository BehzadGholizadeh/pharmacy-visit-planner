# Pharmacy visit planner

Cleans the Iranian pharmacy customer lists (`Customers_*.xlsx`), splits each city into visitor
territories with balanced load, and orders the daily visits.

## Steps
```bash
python clean.py                                   # cleaning -> output/cleaned_data.xlsx
python geocode_neshan.py                          # optional: coordinates from Neshan (needs NESHAN_API_KEY)
python plan_routes.py --per-day 8 --days 22       # visit plan -> output/visit_plan_*.xlsx
```

- Without `work/geocode.csv`, routing is based on the hierarchy of the 10-digit postal code (approximate).
- With coordinates: balanced k-means + shortest path (nearest neighbor + 2-opt).
- Hierarchy: province → county → city → neighborhood. A big city is its own territory, small cities are grouped
  within their own county, and a county that is still small is joined with a neighboring county.
- Neighborhood: from the standard Post address («منطقه ...»), otherwise from the 7/6/5-digit postal-code vote.
- Coordinates are validated with the postal code: a point far from its postal neighbors (same 6/5 digits) is corrected.
- Two outputs: `pharmacies_only` and `all_centers`.

Requirements: Python 3.9+, pandas, numpy, scikit-learn, openpyxl, requests.
