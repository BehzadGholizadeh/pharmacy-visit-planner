# ChatGPT Follow-up Review – Delivery Driver Scope and Route Freeze

**Date:** 2026-10-30  
**Related documents:**
- `docs/reviews/driver-module-readiness-review.md`
- `docs/reviews/grok-response-to-readiness-review.md`
- `docs/product/decisions-v1.md`
- `docs/product/decision-register.md`
- GitHub Issue #1

## 1. Important Product Owner clarification: no route changes during the day

The Product Owner explicitly clarified:

> Route changes are always performed in advance. They do not happen during the working day.

This is a confirmed operating constraint and supersedes the earlier proposal for mid-shift route updates.

### Required system behavior

1. The delivery route is planned, reviewed, published and assigned before the driver's shift begins.
2. The driver downloads and reviews the latest assigned route before starting.
3. Starting the shift locks the route version, stop membership, stop order and driver assignment for that shift.
4. No route reordering, stop insertion/removal or driver reassignment is performed in the active shift.
5. Delivery outcomes and operational exceptions are recorded against the locked route. Recording an event must not mutate the route.
6. Replanning and reassignment happen before a future shift/working day.

### Consequences for the design

- Remove the proposed mid-shift route-diff application and mandatory mid-shift acknowledgement workflow.
- Keep route IDs and versions for traceability, pre-shift publication and audit.
- Add a clear shift-start/route-lock event or timestamp.
- Attach the locked route ID/version to every delivery event.
- Define what the app shows if it is opened after shift start on another device or if the route is missing locally. Do not silently download a different route version and replace an active route.
- Unexpected incidents (customer unavailable, refusal, vehicle issue, damage, missing goods, etc.) become delivery/operational exception events. They do not reorder the active route.
- The exact escalation process for an incident that prevents continuation of the route remains a product decision; it must not be implemented as automatic in-day route replanning.

## 2. Assessment of the new Grok documents

### Confirmed direction

- Separating Visitor (pharmacy visit/order-taking) and Driver (goods delivery) is the correct domain distinction.
- Visitor plans and Driver delivery plans must be independent.
- A Driver route must be sourced from confirmed/ready-to-deliver orders, not from the Visitor's planned pharmacy sequence.
- Phase 1 should focus on the Driver workflow only. Visitor functionality should not be pulled into this MVP without an explicit product decision.
- The existing Python Visitor Planning algorithm must remain unchanged.

### Items that remain incomplete

#### A. Delivery planning input and system ownership

The reviewed repository contains the Visitor planner and its Excel outputs, but no confirmed source of delivery orders, order lines, stock/ready status, delivery manifests or driver assignments.

Before backend/API implementation, identify:
- The authoritative order/ERP/OMS source.
- How an order becomes confirmed and ready to deliver.
- Whether order data includes order lines, quantities, address, contact, payment/credit or delivery constraints.
- Who owns the delivery-planning and publishing boundary.
- Whether routes are manually dispatched in the MVP or automatically optimized.

Manual route creation/assignment before shift start is an acceptable MVP option, but it is a recommendation, not an approved fact.

#### B. Delivery domain model

Do not model a delivery stop as equivalent to one order. One pharmacy stop can contain multiple orders, and each order may contain multiple lines.

At minimum, specify:
- **DeliveryRoute:** service date, assigned driver, version, lifecycle status, ordered stop references and shift lock.
- **DeliveryStop:** pharmacy/destination, sequence, location/contact snapshot, planned arrival estimate and stop outcome.
- **Order:** authoritative order identifier, pharmacy, readiness/dispatch state and delivery state.
- **OrderLine:** product/SKU, ordered quantity, loaded quantity, delivered quantity and returned/remaining quantity as applicable.
- **DeliveryEvent:** immutable event ID, actor/device, route/version, stop/order/line references, event type, quantities, reason, note and timestamps.

Define cardinality, identifier ownership, nullability and the difference between a stop outcome, order outcome and line-level quantity outcome.

#### C. Loading and dispatch

The high-level workflow includes loading, but no specification exists yet. Define:
- Delivery manifest and its source.
- Whether the driver confirms each order or each item.
- How quantity shortages, substitutions, damaged goods and missing items are recorded.
- Whether dispatch requires manager/warehouse confirmation.
- Whether a loaded order can be removed/cancelled and how the goods are reconciled.

Do not assume barcode scanning or a specific warehouse process without confirmation.

#### D. Delivery state machine and evidence

Define separate state transitions for route, stop, order and order line. Clarify Delivered, Partially Delivered, Failed, Refused, Returned and Cancelled, including legal transitions and reason requirements.

Proof-of-delivery remains open: decide whether to collect recipient name, signature, photo, OTP, GPS evidence or none. Do not collect sensitive data or location evidence by default before a purpose and retention policy are approved.

#### E. Unfinished deliveries

Do not carry every unfinished stop forward automatically. The reason and order state matter:
- Customer unavailable may be retryable.
- Refused delivery may require manager review.
- Cancelled orders must not reappear as open deliveries.
- Partial delivery requires remaining order-line quantities to be reconciled.
- Returned goods require inventory/warehouse reconciliation.

Provide a proposed reason-aware policy and keep it marked as pending Product Owner approval.

#### F. Calendar

The agreed timezone and working week must be used by the Delivery planner. Identify the authoritative Iranian holiday calendar and define manager exceptions. Keep this calendar logic separate from the current Visitor planner unless a separate approved change is made.

#### G. Android app packaging

Clarify whether the Driver and Visitor roles are separate application packages or role-based modules/experiences in one app. Phase 1 should implement Driver only either way. Shared code is not the same decision as sharing one installed application.

#### H. Existing documentation drift

The current `driver-module-prd.md` and Phase 1/2/3 documents still contain Visitor pharmacy-visit semantics (Completed/Failed/Skipped, visit service duration, pharmacy visit flow). They must be revised into Delivery Driver requirements before Gemini receives implementation prompts. Do not leave contradictory old and new specifications active without an explicit superseded marker.

## 3. Offline and route-lock requirements

Offline operation remains important, but the model must align with a frozen daily route:

- Download the assigned route and manifest before shift start.
- The shift cannot be started until the required route/manifest snapshot is available locally, unless an explicit offline-start policy is approved.
- Once started, the locally active route version remains fixed for that shift.
- Delivery events are persisted locally before the UI reports success.
- Each event has a stable unique ID and is idempotent on retry.
- Events remain queued until server acknowledgement.
- Sync must not replace the locked route with a newer version.
- Conflicts in order status, duplicate delivery action, cancellation or manager correction need explicit reconciliation rules.
- Account switching must not expose another driver's cached route or outbox.

Define how the system handles the driver starting offline, the server later receiving events, and a pre-shift route change that the device did not download. Do not conflate data sync with route mutation.

## 4. UX areas to specify

Driver-facing minimum screens:
1. Login and session restore.
2. Today's assigned route and summary.
3. Pre-shift route/manifest review.
4. Loading checklist and dispatch confirmation (scope to be decided).
5. Ordered delivery stops and next stop.
6. Stop details with all associated orders.
7. Order and order-line delivery confirmation.
8. Partial/failed/refused/returned flows and reason capture.
9. End-of-shift summary and unresolved exceptions.
10. Sync status, offline/stale data and support/contact states.

Keep Persian-first, RTL, Jalali date display, readable typography, large touch targets and minimal typing in Phase 1.

## 5. Recommended revised phases

### Phase 0 — Product and integration foundation
- Approve the Driver/Visitor role boundary.
- Identify order source, data owner and route publishing boundary.
- Approve the Delivery domain model and status state machines.
- Define route publication/versioning and shift-lock behavior.
- Define manifest/loading responsibilities.
- Define offline event/outbox and sync rules.
- Decide app packaging.
- Correct and verify Android build configuration and test baseline.
- Produce PRD v1.1, architecture, API contract, screen specs, phase prompts and acceptance matrix.

### Phase 1 — Driver workflow with controlled mock data
- Implement Driver-only screens using realistic mock DeliveryRoute, DeliveryStop, Order and OrderLine data.
- Pre-shift route review and shift-start lock.
- Ordered route and next-stop UX.
- Delivery outcomes at order/line level, including partial quantities according to the approved state machine.
- Navigation handoff.
- Local persistence and queued delivery events.
- Tests proving route order/version cannot change during an active shift.

Do not imply that mock login or mock data is production authentication/integration.

### Phase 2 — Real order integration and synchronization
- Integrate the approved order source and delivery route publishing API.
- Driver authentication and assignments.
- Manifest download and loading/dispatch workflow.
- Durable idempotent sync and reconciliation.
- Evidence only according to the approved policy.
- Integration tests for partial delivery, refusal, returns, offline use and account changes.

### Phase 3 — Measurable operational enhancements
- Traffic-aware ETA (clearly an estimate).
- Notifications before shift start for a newly published route.
- End-of-day metrics and unresolved exception reporting.
- Widget/multi-day view.
- Live location only if separately approved after privacy review.

## 6. Required follow-up from Grok

Please update the PRD, architecture and phase documents to reflect the confirmed no-mid-day-route-change constraint.

Deliver a consistent document set with:
- Driver delivery PRD v1.1.
- Decision register with explicit status/owner.
- Delivery domain model and relationship diagram.
- Example route, stop, order, order-line and delivery-event JSON.
- State diagrams for route/shift, stop, order and order line.
- Pre-shift publishing and shift-lock sequence.
- Offline event synchronization sequence.
- Screen-level UX requirements.
- Phase-specific Gemini prompts.
- Acceptance and regression test matrix.

For each unresolved item, show a recommendation and mark it **Pending Product Owner Approval**. Do not begin code implementation or change the existing Python Visitor planner in this review.

## 7. Repository changes made from this review

- Updated `docs/product/decisions-v1.md` to record route freeze at shift start and remove mid-shift route replacement.
- Updated `docs/product/decision-register.md` to reflect the confirmed route-timing rule and list remaining delivery decisions.
- This review document is a review/addendum; it does not authorize implementation.
