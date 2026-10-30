# Decision Register – Driver Module

Last updated: 2026-10-30

| ID | Topic | Status | Decision / Recommendation | Owner |
|----|-------|--------|---------------------------|-------|
| D-01 | Driver vs Visitor roles | **Decided** | Two distinct roles: Visitor takes pharmacy orders; Driver delivers goods | Product Owner |
| D-02 | Plan independence | **Decided** | Visitor plans and Driver delivery plans are independent; do not repurpose the Visitor planner for delivery | Product Owner |
| D-03 | Route change timing | **Decided** | Route is finalized before the driver's shift; no route sequence, stop-membership or driver-assignment changes during the working day; active route is locked at shift start | Product Owner |
| D-04 | Timezone | **Decided** | Asia/Tehran | Product Owner |
| D-05 | Working days | **Decided** | Saturday–Wednesday working; Thursday, Friday and official Iranian public holidays off | Product Owner |
| D-06 | Unfinished deliveries | **Open / Proposed** | Do not blanket auto-carry all unfinished stops. Define reason-aware retry, manager review and order/line-level handling | Grok recommendation; Product Owner approval required |
| D-07 | Route versioning | **Recommended** | Versioned route snapshots; latest version can be published/assigned before shift start; lock at shift start; no mid-shift route-change acknowledgement flow | Grok recommendation; Product Owner approval required |
| D-08 | Pharmacy/customer phone source | **Open** | Source of contact numbers and handling of missing numbers | Product Owner |
| D-09 | Proof of delivery | **Open** | Decide whether recipient confirmation, signature, photo, OTP or other evidence is required | Product Owner |
| D-10 | Live location sharing | **Open** | Recommended to remain out of scope initially; any later use requires explicit privacy/consent design | Product Owner |
| D-11 | Order source and readiness | **Open** | Identify the authoritative source for confirmed orders, ready-to-deliver status and order-line quantities | Product Owner / system owner to be identified |
| D-12 | Loading confirmation | **Open** | Define manifest, loading checks, quantity discrepancies and dispatch confirmation | Product Owner |
| D-13 | Android packaging strategy | **Open** | Decide one role-based app/package or separate Driver and Visitor app packages; shared codebase may still be possible | Product Owner |
| D-14 | Delivery route publishing boundary | **Open** | Define who imports/generates, validates, publishes and assigns delivery routes, and which backend/system owns the API | Product Owner / system owner to be identified |
| D-15 | Delivery state model | **Open** | Define stop, order and order-line states separately, including partial, failed, returned and cancelled outcomes | Product Owner |

---

This register is the single source of truth for product decisions.  
Use **Decided** only for explicit Product Owner decisions. Grok/ChatGPT items must be marked as recommendations until approved. Update this register whenever a decision is made or changed.
