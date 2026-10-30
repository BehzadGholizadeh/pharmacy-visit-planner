# Grok Review – Previous-Day Route Finalization & Offline Start

**Date:** 2026-10-30  
**Responding to:** `docs/reviews/previous-day-route-and-offline-start-review.md` and updated Decision Register / decisions-v1.md

---

## 1. Assessment of the new rule

The Product Owner clarification is clear and architecturally strong:

> The route is finalized the day before. After finalization the manager cannot change it. The warehouse prepares from that same manifest. The driver downloads the same snapshot the previous day and can therefore start offline.

This is **better** than a shift-start lock model because:

- Warehouse and driver work from exactly the same frozen snapshot.
- Offline start becomes a natural consequence, not a special case.
- There is a clean immutability boundary (`finalized_at`) that is independent of when the driver presses “Start”.

I fully accept this as a **core architectural rule**.

---

## 2. Validation against current documents

| Document | Consistency with new rule |
|----------|---------------------------|
| `decisions-v1.md` | Good – section 3 and 4 correctly describe previous-day finalization and offline start |
| `decision-register.md` | Good – D-03 Decided, D-12 Partially Decided, D-16 Recommended |
| PRD v1.1 | Needs a small alignment pass (still contains some “lock at shift start” language in places) |
| Domain model | Needs `finalized_at` vs `shift_started_at` clearly separated |
| Data contract examples | Needs a “Finalized previous-day snapshot” example that includes both route and manifest |
| State machines | Needs Finalized status before Active |
| Phase 0 / Phase 1 | Need explicit offline-start acceptance criteria |

---

## 3. Required modeling corrections (already directionally correct)

Keep these timestamps **distinct**:

| Timestamp | Meaning |
|-----------|---------|
| `finalized_at` | Previous day – route + manifest become immutable |
| `downloaded_at` | When the driver device successfully persisted the snapshot |
| `prepared_at` | Warehouse preparation recorded (optional for MVP) |
| `shift_started_at` | Actual moment the driver starts the service-day shift |

**Invariant:**  
After `finalized_at`, no system (manager UI, API, warehouse, or driver app) may alter stop membership, order, sequence, driver assignment or manifest quantities for that `service_date`.

Shift start only records that the driver has begun work against an already-frozen snapshot.

---

## 4. Offline-start rule (recommended exact wording)

**A driver may start the shift offline if and only if:**

1. A route with status `Finalized` (or `Assigned`) exists locally.
2. `service_date` equals today in `Asia/Tehran`.
3. `assigned_driver_id` matches the authenticated local session.
4. Matching `manifest_id` + `manifest_version` is present and consistent with the route.
5. Integrity checks on the snapshot pass (no missing required stops/orders/lines).

If any condition fails → **block** shift start and show a clear message (“مسیر نهایی روز قبل روی دستگاه موجود نیست. لطفاً آنلاین شوید یا با پشتیبانی تماس بگیرید.”).

Once the shift has started, sync may upload events but **must never** replace the local frozen snapshot.

---

## 5. What is still open (does not block accepting the rule)

These remain open and are correctly marked in the Decision Register:

- Exact cutoff time for previous-day finalization (e.g. 18:00 Asia/Tehran).
- Detailed warehouse picking / discrepancy process (D-12).
- Order source (D-11).
- Proof of delivery (D-09).
- Delivery state machine details (D-15).
- Unfinished-delivery future-day retry policy (D-06).
- App packaging (D-13).

None of these invalidate the previous-day finalization rule.

---

## 6. Readiness judgment

| Question | Answer |
|----------|--------|
| Is the previous-day finalization rule clear and consistent? | **Yes** |
| Is offline start correctly derived from that rule? | **Yes** |
| Are warehouse and driver forced to the same snapshot? | **Yes** |
| Can we close Phase 0 right now? | **Almost** – remaining Decision Register items should be either decided or explicitly accepted as “mock-only for Phase 1” |
| Can we start Gemini coding today? | **No** – still need Phase 0 exit criteria formally closed |

---

## 7. Recommended immediate next steps

1. Product Owner confirms D-16 (offline start rule) as **Decided** (or accepts the wording above).
2. Optionally set a default previous-day cutoff time (recommendation: 18:00 Asia/Tehran the day before).
3. Mark which of D-06, D-09, D-11, D-12, D-13, D-15 are:
   - Decided now, or
   - Explicitly deferred and allowed to be mocked in Phase 1.
4. After that, Grok will produce a final Phase 0 closure package and the Phase 1 Gemini prompt will be unlocked.

No Android or Python code has been changed.

---

**Status:** Previous-day finalization rule accepted as core architecture. Waiting for Product Owner confirmation on D-16 and the “mock vs decide” status of remaining open items before closing Phase 0.
