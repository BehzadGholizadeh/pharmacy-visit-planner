# Product Decisions – Driver & Visitor Modules (v1)

**Date:** 2026-10-30  
**Status:** Approved by Product Owner (via chat)  
**Timezone:** Asia/Tehran (explicit)

---

## 1. Roles (Confirmed)

There are **two distinct roles**:

| Role | Persian | Responsibility |
|------|---------|----------------|
| **Visitor** | ویزیتور | Goes to the pharmacy, takes orders / does the visit |
| **Driver** | راننده | Loads the goods according to confirmed orders and delivers them |

- One person can potentially have both roles over time, but the system treats them as separate assignments.
- A Visitor plan and a Driver plan are independent.
- The Driver sees the **delivery route** based on the current order/delivery status, not the original visit plan.

---

## 2. Plan Independence

- Visit plans (for Visitors) are generated and updated independently.
- Delivery plans (for Drivers) are generated based on **confirmed / ready-to-deliver orders**.
- Routes are **not permanently fixed**. They can change between cycles or even mid-cycle based on:
  - New orders
  - Cancelled orders
  - Stock availability
  - Traffic / operational constraints
  - Manager re-assignment

---

## 3. Driver Workflow (High-level)

1. Driver opens the app before starting the shift.
2. Sees the list of deliveries that are **ready** (based on order status).
3. Loads the goods.
4. Starts the route (ordered stops).
5. Delivers, marks status (Delivered / Failed / Partial / Returned).
6. Syncs when network is available.

---

## 4. Calendar & Working Days (Confirmed)

- **Timezone:** `Asia/Tehran`
- **Working days:** Saturday, Sunday, Monday, Tuesday, Wednesday
- **Non-working days:**
  - Thursday
  - Friday
  - Official Iranian public holidays (تقویم رسمی ایران)

Any generated plan must respect this calendar.

---

## 5. Unfinished Visits / Deliveries – Recommendation

**Recommended policy (for approval):**

| Situation | Behavior |
|-----------|----------|
| Stop not completed by end of day | Marked as **Overdue** |
| Next working day | Automatically appears at the top of the new day’s list (or in a separate “Overdue” section) with higher priority |
| After 2 consecutive working days still open | Requires **Manager action** (re-assign, cancel, or force complete) |
| Manager can always manually move, cancel or re-assign any open stop |

This keeps the system automatic for normal cases while giving the manager control for exceptions.

---

## 6. Route Versioning (Recommended)

Every published route must have:
- `route_id`
- `version`
- `published_at`
- `assigned_to` (driver or visitor account)
- `status`: Draft → Published → Assigned → Active → Completed / Cancelled / Superseded

If a new version is published while the driver is already on the road:
- Driver receives a notification.
- Must acknowledge the change.
- Already completed stops are preserved.
- Remaining stops are replaced by the new version.

---

## 7. Open Items Still Needing Decision

- Exact source of pharmacy phone numbers (currently missing in clean.py).
- Whether photo proof is mandatory for delivery or optional.
- Whether live location sharing will ever be enabled (currently recommended as non-goal).

---

**Next step:** ChatGPT / product review of this decision document, then finalization of PRD v1.1 and data contract.
