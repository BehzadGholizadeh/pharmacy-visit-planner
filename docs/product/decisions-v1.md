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
| **Driver** | راننده | Loads goods for confirmed orders and delivers them |

- One person may potentially hold both roles over time, but the system treats the roles and assignments separately.
- A Visitor plan and a Driver delivery plan are independent.
- The Driver sees a **delivery route** based on orders that are confirmed and ready for delivery, not the original Visitor visit plan.

## 2. Plan Independence (Confirmed)

- Visitor plans are generated and updated independently.
- Driver delivery plans are generated from confirmed / ready-to-deliver orders.
- The delivery-planning workflow is separate from the existing Python Visitor Planning algorithm.
- New orders, cancellations, stock changes and manager reassignment may affect a delivery plan **before the relevant driver's shift starts**.
- The existing Visitor Planning algorithm and its behavior must not be changed as part of the Driver app work.

## 3. Route Change Timing and Daily Lock (Confirmed)

**A driver's route is finalized before the driver's working day/shift begins. Route changes do not take place during the working day.**

- Route order, stop membership and driver assignment must be finalized and published before the shift starts.
- When the driver starts the shift, the assigned route version becomes the active, locked route for that shift.
- The app and backend must not reorder stops, add/remove stops, or reassign the active route during that shift.
- Operational outcomes during the day (for example delivered, partial, failed, returned, customer unavailable or vehicle issue) are recorded as delivery events against the locked route. They do not modify the route sequence.
- A failed or exceptional delivery is handled through its delivery status and the agreed manager follow-up process; it is not automatically converted into a same-day route change.
- Any new planning/reassignment is performed before a future shift/working day.

This rule replaces any earlier wording that allowed a new route version to be pushed, acknowledged or applied while a driver was already on the road.

## 4. Driver Workflow (High-level)

1. Before the shift, the manager/planning process finalizes and assigns the delivery route.
2. The driver opens the app and sees the route assigned for the current working day.
3. The driver reviews the stops and the orders/items expected at each stop.
4. The driver loads goods according to the approved delivery manifest and records any required loading discrepancy.
5. The driver starts the shift; the route version is locked for that shift.
6. The driver follows the ordered stops and records delivery outcomes (Delivered / Partially Delivered / Failed / Returned, subject to the approved state model).
7. Events are saved locally and synchronized when network access is available.

## 5. Calendar & Working Days (Confirmed)

- **Timezone:** `Asia/Tehran`
- **Working days:** Saturday, Sunday, Monday, Tuesday, Wednesday
- **Non-working days:** Thursday, Friday and official Iranian public holidays.

Any delivery plan must respect this calendar. The authoritative holiday-calendar source and manager override process still need to be specified.

## 6. Unfinished Deliveries (Open – Do Not Assume Automatic Carry-Over)

A blanket automatic carry-over policy has **not** been approved.

The handling of an unfinished delivery must consider:
- The delivery outcome/reason.
- Whether the order was loaded and dispatched.
- Whether all or only some order lines were delivered.
- Whether the order was cancelled, returned, refused or is still eligible for retry.
- Whether manager review or reassignment is required.

Do not automatically put every unfinished stop at the top of the next day's route. Define a reason-aware policy and obtain Product Owner approval before implementing automatic carry-over.

## 7. Route Identity and Versioning (Recommended)

Every published delivery route should have:
- `route_id`
- `version`
- `service_date` (actual calendar date, not only a cycle-relative day)
- `published_at`
- `assigned_driver_id`
- `status`: Draft → Published → Assigned → Active → Completed / Cancelled / Superseded
- `locked_at` or equivalent shift-start marker

Recommended behavior:
- A new version may replace a previously published route **only before the driver's shift starts**.
- The driver downloads the latest assigned version before starting the shift.
- At shift start, the route snapshot is locked and its route ID/version is attached to delivery events.
- No mid-shift route-change notification or acknowledgement workflow is required because mid-shift route changes are not part of the operating model.

## 8. Open Items Still Needing Decision

- Authoritative source for confirmed/ready-to-deliver orders and order-line quantities.
- Ownership and implementation boundary for importing/publishing delivery routes to the app.
- Pharmacy/customer phone number source (not present in the reviewed `clean.py` source-column mapping).
- Loading confirmation process (manual confirmation, item scan, quantity check, or another process).
- Proof-of-delivery policy (recipient name, signature, photo, OTP, none, or a combination).
- Exact delivery status/state machine and partial-delivery rules.
- Reason-aware retry / unfinished-delivery policy.
- Whether Driver and Visitor roles use one Android app with role-based experiences or separate app packages.
- Whether live location sharing will ever be enabled; recommended to remain out of scope for the initial release.

---

**Next step:** finalize the open items and the delivery data contract, then approve the revised PRD and Phase 0 exit criteria. No implementation authorization is implied by this document.
