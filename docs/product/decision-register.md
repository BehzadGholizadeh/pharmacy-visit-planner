# Decision Register – Driver Module

Last updated: 2026-10-30

| ID | Topic | Status | Decision / Recommendation | Owner |
|----|-------|--------|---------------------------|-------|
| D-01 | Driver vs Visitor roles | **Decided** | Two distinct roles: Visitor takes pharmacy orders; Driver delivers goods | Product Owner |
| D-02 | Plan independence | **Decided** | Visitor plans and Driver delivery plans are independent; do not repurpose the Visitor planner for delivery | Product Owner |
| D-03 | Previous-day route finalization | **Decided** | Delivery route is finalized and assigned on the previous day. After finalization the manager cannot edit, reorder, add/remove stops or orders, reassign the driver or publish a replacement version for that service date | Product Owner |
| D-04 | Timezone | **Decided** | Asia/Tehran | Product Owner |
| D-05 | Working days | **Decided** | Saturday–Wednesday working; Thursday, Friday and official Iranian public holidays off | Product Owner |
| D-06 | Unfinished deliveries | **Open / Proposed** | No blanket carry-over. Define reason-aware future-day retry and manager review; current frozen route is never modified | Grok recommendation; Product Owner approval required |
| D-07 | Route identity/version | **Recommended** | Keep route ID/version for audit; route and manifest versions are frozen together on previous-day finalization. Shift start is separate from finalization | Grok recommendation; Product Owner approval required |
| D-08 | Pharmacy/customer phone source | **Open** | Source of contact numbers and handling of missing numbers | Product Owner |
| D-09 | Proof of delivery | **Open** | Decide whether recipient confirmation, signature, photo, OTP or other evidence is required | Product Owner |
| D-10 | Live location sharing | **Open** | Recommended to remain out of scope initially; any later use requires explicit privacy/consent design | Product Owner |
| D-11 | Order source and readiness | **Open** | Identify the authoritative source for confirmed orders, ready-to-deliver status and order-line quantities | Product Owner / system owner to be identified |
| D-12 | Previous-day warehouse preparation | **Partially Decided** | Warehouse prepares goods on the previous day using the exact finalized route manifest. Picking/checking/staging/dispatch steps and discrepancy handling remain open | Product Owner |
| D-13 | Android packaging strategy | **Open** | Decide one role-based app/package or separate Driver and Visitor app packages; shared codebase may still be possible | Product Owner |
| D-14 | Delivery route publishing boundary | **Open** | Define who imports/generates, validates and publishes the route/manifest snapshot and which backend/system owns the API | Product Owner / system owner to be identified |
| D-15 | Delivery state model | **Open** | Define stop, order and order-line states separately, including partial, failed, refused, returned and cancelled outcomes | Product Owner |
| D-16 | Offline shift start | **Recommended – derived from D-03/D-12** | Driver may start offline only when the previous-day finalized route and its matching manifest have already been downloaded and persisted locally. If missing/incomplete/mismatched, block start and require sync/support | Product Owner to confirm exact operational fallback |
| D-17 | Finalized snapshot integrity | **Recommended** | Route and manifest share immutable route/version references; warehouse and driver use the same snapshot; delivery events reference that exact snapshot | Grok recommendation; Product Owner approval required |

---

This register is the single source of truth for product decisions.  
Use **Decided** only for explicit Product Owner decisions. Recommendations and derived technical rules remain marked as pending until explicitly approved. Update this register whenever a decision is made or changed.
