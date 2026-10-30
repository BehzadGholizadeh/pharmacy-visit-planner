# Product Decisions – Driver & Visitor Modules (v1)

**Date:** 2026-10-30  
**Status:** Product-owner decisions and proposals; see the Decision Register for each item's approval state.  
**Timezone:** Asia/Tehran

---

## 1. Roles (Confirmed)

There are **two distinct roles**:

| Role | Persian | Responsibility |
|------|---------|----------------|
| **Visitor** | ویزیتور | Visits pharmacies and takes orders / performs the visit |
| **Driver** | راننده | Delivers goods for confirmed orders |

- One person may potentially hold both roles over time, but the system treats the roles and assignments separately.
- A Visitor plan and a Driver delivery plan are independent.
- The Driver sees a **delivery route** based on confirmed and ready-to-deliver orders, not the original Visitor visit plan.

## 2. Plan Independence (Confirmed)

- Visitor plans are generated and updated independently.
- Driver delivery plans are generated from confirmed / ready-to-deliver orders.
- The delivery-planning workflow is separate from the existing Python Visitor Planning algorithm.
- The existing Python Visitor Planning algorithm and its behavior must not be changed as part of the Driver app work.

## 3. Previous-Day Route Finalization and Daily Immutability (Confirmed)

**The delivery route is determined and finalized on the day before the service date. Once finalized, the manager is not permitted to change it. The warehouse also prepares the goods on the previous day using that same finalized delivery manifest.**

The following rules apply:

1. On the previous day, the delivery route is prepared, reviewed, finalized and assigned to the driver.
2. The final route includes the driver assignment, the complete ordered stop list, the orders assigned to each stop, and the delivery manifest/order-line quantities required for that day's deliveries.
3. The final route and its corresponding manifest are published as one consistent, versioned planning snapshot.
4. The warehouse receives/uses that exact finalized manifest and prepares the goods on the previous day. The warehouse must not prepare against a different route or manifest version.
5. The driver app downloads and locally persists the finalized route and matching manifest on the previous day, so they are available even when the driver has no internet access on the service date.
6. After finalization, the manager must not edit the route, change its stop order, add/remove stops or orders, change the assigned driver, or publish a replacement version for that service date.
7. Starting the shift on the service date records that the driver has started. It does **not** create the route lock; the route was already frozen on the previous day.
8. During the service date, delivery outcomes and operational exceptions are recorded as events against the frozen route and manifest. Events do not mutate the route or silently change the manifest.
9. A preparation discrepancy discovered by the warehouse must be surfaced and resolved through an explicit exception process. It must not silently alter the frozen route/manifest. The detailed warehouse discrepancy process remains open.
10. Any new planning or reassignment must happen before the route is finalized for a future service date.

This rule supersedes earlier wording that suggested the route only becomes immutable when the driver presses Start Shift or that a newer route version can replace it before the same shift starts.

## 4. Offline Start Policy (Derived Product Requirement; confirm operational details in Phase 0)

Because the route and manifest are finalized and prepared the previous day:

- The driver **may start and complete the shift offline** when the exact finalized route and matching manifest have already been downloaded and persisted on the device.
- The app must verify locally that the route is finalized, assigned to the authenticated driver, for the current service date in Asia/Tehran, and paired with the matching manifest/route version.
- Shift start and delivery events must be saved locally even when there is no network. Events are synchronized later without duplication.
- If the device does not contain the finalized route and matching manifest, or the local data is incomplete/corrupt/for another driver or date, the app must not pretend it can safely start offline. It should show a clear blocking message and require synchronization/support before dispatch.
- The app must never replace a route already in use with another route version during the service date.

## 5. Driver Workflow (High-level)

1. **Previous day – Planning:** prepare, review, finalize and assign the next service day's route.
2. **Previous day – Warehouse:** prepare the goods using the exact manifest linked to that finalized route.
3. **Previous day – Driver device:** download and verify the finalized route and matching manifest; show that the next shift is ready for offline use.
4. **Service date – Start:** driver opens the app and starts the shift using the locally available frozen snapshot, online or offline.
5. Driver follows the fixed stop order and records delivery outcomes (Delivered / Partially Delivered / Failed / Refused, subject to the approved state model).
6. Events are saved locally first and synchronized when network access is available.

## 6. Calendar & Working Days (Confirmed)

- **Timezone:** Asia/Tehran
- **Working days:** Saturday, Sunday, Monday, Tuesday, Wednesday
- **Non-working days:** Thursday, Friday and official Iranian public holidays.

Any delivery plan must respect this calendar. The authoritative holiday-calendar source and manager override process still need to be specified.

## 7. Unfinished Deliveries (Open – Do Not Assume Automatic Carry-Over)

A blanket automatic carry-over policy has **not** been approved.

The handling of an unfinished delivery must consider:
- The delivery outcome/reason.
- Whether the order was included in the previous-day frozen manifest and prepared by the warehouse.
- Whether all or only some order lines were delivered.
- Whether the order was refused, partially delivered, cancelled before finalization, or remains eligible for retry.
- Whether manager review or reassignment is required for a **future service date**.

Do not automatically modify the current day's frozen route or put every unfinished stop into the next day's route. Future-day retry must be planned and finalized as part of that future day's previous-day planning process.

## 8. Route Identity and Versioning (Recommended)

Every finalized delivery route should have:
- route_id
- version
- service_date (actual calendar date in Asia/Tehran)
- published_at
- finalized_at
- finalized_by
- assigned_driver_id
- manifest_id and manifest_version
- status: Draft → Finalized/Assigned → Active → Completed
- shift_started_at (set when the driver starts; distinct from finalization)

Recommended invariants:
- Versions may be revised while the plan is still a draft and before finalization.
- Finalization on the previous day freezes the route and corresponding manifest for that service date.
- No post-finalization route or manifest replacement is allowed for that service date.
- Every shift-start and delivery event references the finalized route_id, version, manifest_id and manifest_version.
- A driver can start offline only from the exact finalized snapshot already stored locally.

## 9. Open Items Still Needing Decision

- Authoritative source for confirmed/ready-to-deliver orders and order-line quantities.
- Ownership and implementation boundary for importing/publishing delivery routes to the app.
- Pharmacy/customer phone number source (not present in the reviewed clean.py source-column mapping).
- Detailed warehouse picking, checking, staging and dispatch confirmation process; the previous-day preparation requirement itself is confirmed.
- How warehouse preparation discrepancies are escalated before dispatch without editing the finalized route/manifest.
- Proof-of-delivery policy (recipient name, signature, photo, OTP, none, or a combination).
- Exact delivery status/state machine and partial-delivery rules.
- Reason-aware retry / unfinished-delivery policy for future service dates.
- Whether Driver and Visitor roles use one Android app with role-based experiences or separate app packages.
- Whether live location sharing will ever be enabled; recommended to remain out of scope for the initial release.

---

**Next step:** update the PRD, domain model, data contract and Phase 0/1 documents with previous-day finalization, warehouse preparation and offline-start behavior. No implementation authorization is implied by this document.
