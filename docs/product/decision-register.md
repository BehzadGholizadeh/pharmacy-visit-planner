# Decision Register – Driver Module

Last updated: 2026-10-30 (Product Owner final decisions applied)

| ID | Topic | Status | Decision |
|----|-------|--------|----------|
| D-01 | Driver vs Visitor roles | **Decided** | Two distinct roles: Visitor takes pharmacy orders; Driver delivers goods |
| D-02 | Plan independence | **Decided** | Visitor plans and Driver delivery plans are independent |
| D-03 | Previous-day route finalization | **Decided** | Route + matching manifest finalized the day before. After finalization manager cannot edit, reorder, add/remove stops/orders, reassign driver or publish replacement for that service date |
| D-04 | Timezone | **Decided** | Asia/Tehran |
| D-05 | Working days | **Decided** | Sat–Wed working; Thu, Fri + official Iranian public holidays off |
| D-06 | Unfinished deliveries | **Accepted for Phase 1 Mock only** | No automatic carry-over. End-of-day unresolved orders → Pending Manager Review. Manager may include them in a future day’s planning. Active day route is never modified. Production retry policy deferred to Phase 2 |
| D-07 | Route/manifest versioning | **Decided** | Immutable route + manifest versioning for audit. No post-finalization replacement |
| D-08 | Phone numbers | **Decided** | Phone is optional. Null → no call action shown |
| D-09 | Proof of delivery | **Accepted for Phase 1 Mock only** | No photo, signature, OTP or GPS in Phase 1. Simple delivery action/event is sufficient. Not represented as production-grade proof |
| D-10 | Live location | **Deferred to Phase 2+ / Out of scope** | Live location tracking out of scope for Phase 1 and Phase 2 |
| D-11 | Order source | **Accepted for Phase 1 Mock only** | Deterministic local Mock Repository with realistic multi-order / multi-line data. No ERP or live API |
| D-12 | Warehouse preparation | **Core rule Decided; detailed workflow Mock only** | Warehouse prepares previous day from exact finalized manifest. Phase 1 shows read-only Prepared status and requires it before shift start. No barcode/inventory/real warehouse integration in Phase 1 |
| D-13 | Android packaging | **Decided** | One standalone Driver app: `com.pharmacyvisit.driver`. No Visitor features in this MVP |
| D-14 | Publishing boundary / API | **Accepted for Phase 1 Mock only** | Local mock repository. Production API ownership deferred |
| D-15 | Delivery state model | **Accepted for Phase 1 Mock only** | Simplified states (see State Machines doc). Failed/Refused/Partial require reason. Returned and physical return workflow deferred. Cancellation after finalization must not mutate route/manifest |
| D-16 | Offline shift start | **Decided** | Allowed only when exact previous-day finalized route + matching manifest are fully persisted locally, assigned to authenticated driver, valid for current Asia/Tehran service date, and marked Prepared. Missing/incomplete/corrupt/mismatched → block start |
| D-17 | Snapshot integrity | **Decided** | Route and manifest form one consistent immutable snapshot. Local integrity check in Mock; server-signed verification designed for production |

Status legend: **Decided** | **Accepted for Phase 1 Mock only** | **Deferred to Phase 2** | **Open**
