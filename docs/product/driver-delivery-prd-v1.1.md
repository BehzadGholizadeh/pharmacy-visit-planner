# Driver Delivery Module – PRD v1.1

**Status:** Draft for Product Owner + ChatGPT review  
**Date:** 2026-10-30  
**Timezone:** Asia/Tehran  
**Scope:** Driver (delivery) role only. Visitor (order-taking) is out of scope for this PRD.

---

## 1. Goal

Enable a driver to:
1. See the delivery route assigned for the current working day.
2. Review the manifest and load goods before starting.
3. Start the shift (locking the route).
4. Follow the ordered stops and record delivery outcomes (including partial quantities).
5. Work reliably offline and sync later.

## 2. Confirmed Operating Rules

| Rule | Status |
|------|--------|
| Two separate roles: Visitor vs Driver | Decided |
| Visitor plans and Driver delivery plans are independent | Decided |
| Route is finalized **before** shift start | Decided |
| At shift start the route is **locked** (no add/remove/reorder/reassign during the day) | Decided |
| Operational outcomes are recorded as events against the locked route | Decided |
| Timezone Asia/Tehran | Decided |
| Working days: Sat–Wed; Thu, Fri + official Iranian holidays off | Decided |
| Existing Python Visitor planner must not be changed | Decided |

## 3. Core Concepts

- **DeliveryRoute**: one driver’s ordered list of stops for one service date + version + lock state.
- **DeliveryStop**: one destination (usually a pharmacy) containing one or more orders.
- **Order**: business order that is ready for delivery.
- **OrderLine**: individual product/SKU line with quantities.
- **DeliveryEvent**: immutable record of an action (load, deliver, partial, fail, return…).

## 4. High-level Driver Flow

1. Pre-shift: download latest assigned route + manifest.
2. Review stops and items.
3. Perform loading checks (scope still open – see Decision Register).
4. Press “Start Shift” → route becomes Active/Locked.
5. Navigate stop-by-stop.
6. At each stop record outcomes at Order / OrderLine level.
7. End of day: summary of completed, partial, failed, returned items + pending sync status.

## 5. Explicit Non-Goals (Initial Release)

- Changing route sequence or membership during an active shift.
- Live location tracking / sharing.
- Visitor (order-taking) features.
- Automatic same-day replanning.
- Reading the Python planner’s Excel files directly as the production data source.

## 6. Open Items (must be closed before production backend work)

See `docs/product/decision-register.md` items D-06, D-08 to D-15.

Most critical:
- Authoritative source of ready-to-deliver orders and order lines.
- Loading confirmation process.
- Delivery / partial / return state machine details.
- Proof-of-delivery policy.
- Unfinished-delivery (retry) policy.
- App packaging (one app vs two packages).

## 7. Success Metrics (MVP)

- Driver can start a shift with a locked route in < 30 seconds after opening the app (when data is already downloaded).
- 100% of delivery actions are persisted locally before UI success feedback.
- No route mutation is possible after shift start (enforced by tests).
- Offline work for a full day is possible; events sync without duplication when connectivity returns.
