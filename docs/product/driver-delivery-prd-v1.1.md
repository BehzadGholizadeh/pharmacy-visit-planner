# Driver Delivery Module – PRD v1.1

**Status:** Draft for Product Owner + ChatGPT review  
**Date:** 2026-10-30  
**Timezone:** Asia/Tehran  
**Scope:** Driver (delivery) role only. Visitor (order-taking) is out of scope for this PRD.

---

## 1. Goal

Enable a driver to:
1. Receive the finalized delivery route and manifest on the previous day.
2. Review the stops and expected goods before the service date.
3. Start the service-day shift online or offline using the pre-downloaded finalized snapshot.
4. Follow the fixed stop order and record delivery outcomes (including partial quantities).
5. Work reliably offline for the full shift and synchronize events later.

## 2. Confirmed Operating Rules

| Rule | Status |
|------|--------|
| Two separate roles: Visitor vs Driver | Decided |
| Visitor plans and Driver delivery plans are independent | Decided |
| Delivery route is finalized and assigned on the previous day | Decided |
| Manager cannot change route, stop order, stop membership, orders or driver assignment after finalization | Decided |
| Warehouse prepares goods on the previous day using the same finalized manifest | Decided |
| Driver route and matching manifest are downloaded and persisted on the previous day | Required behavior derived from the operating rule |
| Service-day shift may start offline if the exact finalized snapshot is available locally | Recommended technical policy; confirm exact fallback in Phase 0 |
| Shift start records operational start; it does not create the route freeze | Decided consequence of previous-day finalization |
| Operational outcomes are recorded as events against the frozen snapshot | Decided |
| Timezone Asia/Tehran | Decided |
| Working days: Sat–Wed; Thu, Fri + official Iranian holidays off | Decided |
| Existing Python Visitor planner must not be changed | Decided |

## 3. Core Concepts

- **DeliveryRoute**: one driver's ordered list of stops for one service date and immutable finalized version.
- **DeliveryStop**: one destination (usually a pharmacy) containing one or more orders.
- **Order**: business order included in the previous-day finalized manifest.
- **OrderLine**: individual product/SKU line with quantities.
- **DeliveryManifest**: exact set of orders and expected goods associated with a finalized route/version and used by the warehouse for previous-day preparation.
- **DeliveryEvent**: immutable record of a shift or delivery action. Every event references the route and manifest snapshot it belongs to.

## 4. Previous-Day and Service-Day Workflow

### Previous day (planning, warehouse and driver preparation)

1. Prepare and review the next service day's delivery route.
2. Resolve known order/stock/preparation discrepancies before finalization.
3. Finalize and assign the route. The route, stop order, stop membership, orders and manifest become immutable for that service date.
4. Publish the exact route/manifest snapshot to the warehouse for goods preparation.
5. Warehouse prepares/stages goods using that manifest. Any discrepancy is reported as an exception; it must not silently alter the frozen route or manifest.
6. Driver app downloads the same finalized route and manifest and persists them locally.
7. App shows a clear “Ready for next shift / Available offline” state only after both snapshots are complete and consistent.

### Service date (driver execution)

1. Driver opens the app and reviews the locally stored route and manifest.
2. Driver starts the shift online or offline, only if the finalized route and matching manifest are present, complete and assigned to that driver/date.
3. Shift start is recorded locally. The route is already frozen; no route mutation is allowed.
4. Driver follows the ordered stops and records outcomes at order/order-line level.
5. Delivery events are persisted locally before success feedback and synchronized when connectivity is available.
6. End-of-day summary displays delivery outcomes and pending synchronization.

## 5. Offline-Start Rules

- Offline start is allowed when the device has already downloaded and persisted the exact finalized route and its matching manifest on the previous day.
- The app verifies local route status, driver assignment, service date in Asia/Tehran, route version, manifest ID/version and snapshot completeness.
- The app does not need a live server check at shift start because the operating rule prohibits post-finalization changes for that service date.
- If the required snapshot is missing, corrupt, incomplete, for another driver/date, or route/manifest references do not match, the app blocks shift start and shows an actionable message.
- Once a shift starts, background sync may upload events but must never replace or alter the route/manifest snapshot.
- Events are stored locally first, use stable IDs for idempotent retry, and remain pending until acknowledged by the server.

## 6. Explicit Non-Goals (Initial Release)

- Changing route sequence, stop membership, order membership or driver assignment after previous-day finalization.
- Mid-shift route diff, route replacement or route-change acknowledgement workflow.
- Live location tracking / sharing.
- Visitor (order-taking) features.
- Automatic same-day replanning.
- Reading the Python planner's Excel files directly as the production delivery data source.

## 7. Open Items (must be closed before production backend work)

See docs/product/decision-register.md items D-06, D-08 to D-17.

Most critical:
- Authoritative source of ready-to-deliver orders and order lines.
- Detailed warehouse picking/checking/staging and discrepancy workflow.
- Delivery / partial / return state machine details.
- Proof-of-delivery policy.
- Unfinished-delivery retry policy for future dates.
- App packaging (one app vs two packages).
- Route/manifest publishing boundary and authoritative owner.

## 8. Success Metrics (MVP)

- Driver can open the app and start an already-prepared shift in < 30 seconds.
- 100% of delivery actions are persisted locally before UI success feedback.
- 100% of offline shift starts use a locally stored, complete and matching finalized route + manifest.
- No route or manifest mutation is possible after previous-day finalization (enforced by tests).
- Offline work for a full day is possible; events synchronize without duplication when connectivity returns.
