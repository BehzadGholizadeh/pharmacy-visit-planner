# Pharmacy visit planner

Cleans the Iranian pharmacy customer lists (`Customers_*.xlsx`), divides them into visitor zones by
province → county → city → neighborhood, and builds each visitor's daily schedule on a time budget
(visit time + travel + traffic).

## Steps
```bash
python clean.py                                   # cleaning -> output/cleaned_data.xlsx
python population.py                              # city population and coordinates (Wikidata) -> data/city_population.csv
python geocode_neshan.py                          # optional: pharmacy coordinates from Neshan (needs NESHAN_API_KEY)
python plan_routes.py --hours 9 --days-per-week 5 --weeks 4
```

## Time model (`timing.py`)
- Working day: 9 hours minus a 30-minute break = 510 minutes, starting at 08:00; 5 days a week; visit cycle 4 weeks (20 working days).
- City size from the census population (Wikidata):

| Class | Population | Traffic speed | Parking + walking |
|---|---|---|---|
| Metropolis | ≥ 1M (Tehran 13 km/h) | 17 km/h | 7 min |
| Big city | 250k–1M | 22 km/h | 5 min |
| Medium city | 50k–250k | 27 km/h | 3 min |
| Small town / village | < 50k | 32 km/h | 2 min |

- Time inside the pharmacy: 30 minutes in big cities and crowded neighborhoods, 20 minutes in quiet areas
  (in a medium city, a neighborhood with the most centers = crowded).
- Distance between two neighboring pharmacies, without coordinates: `0.7124·√(area/N) × 1.35` (city area estimated from population and density).
- Between towns: distance between the town coordinates × 1.35 at 60 km/h. A zone's towns are at most 60 km from its main town.
- A visitor is assigned whole days: a big city gets its own visitor(s); small zones of one province are chained by proximity and packed into one visitor.

- Without `work/geocode.csv`, the order follows the hierarchy of neighborhood and postal code; with coordinates: Hilbert curve + shortest path (2-opt).
- Coordinates are validated with the postal code (a point far from records with the same 6/5 postal digits is corrected).
- Two outputs: `pharmacies_only` and `all_centers`.

Requirements: Python 3.9+, pandas, numpy, scikit-learn, openpyxl, requests.
