# Phase 0 – Product & Integration Foundation

**Goal:** Close critical product and architecture decisions so that Phase 1 (Driver MVP with mock data) can be implemented safely.

## Exit Criteria (must all be true)

- [ ] Decision Register items D-06, D-08–D-17 have explicit Product Owner decisions or are explicitly accepted as mock-only / deferred to Phase 2.
- [ ] Delivery domain model and state machines are approved for the Phase 1 mock scope.
- [ ] Example JSON data contract is approved or explicitly marked “good enough for mock”.
- [ ] Previous-day route finalization and immutability rule is reflected in all active documents.
- [ ] Warehouse uses the exact finalized route-linked manifest and prepares goods on the previous day; detailed warehouse workflow is either approved or explicitly mock-only.
- [ ] Driver can download and persist the finalized route + matching manifest on the previous day.
- [ ] Offline-start rule is explicit: allow offline start only from a complete, locally persisted, matching finalized snapshot; otherwise block with an actionable message.
- [ ] Shift start is distinct from route finalization; no route lock is postponed until the driver presses Start Shift.
- [ ] Android build configuration (Kotlin + Compose) is verified and Gradle wrapper is present.
- [ ] PRD v1.1, domain model, data-contract examples, state machines and Phase 1 prompt are consistent.
- [ ] No contradictory Visitor-centric language remains in active Driver documents (or is clearly marked superseded).

## Deliverables of this phase

1. Approved Decision Register.
2. driver-delivery-prd-v1.1.md
3. Domain model + state machines + JSON examples.
4. Previous-day warehouse preparation and driver pre-sync workflow.
5. Updated Phase 1 prompt for Gemini (Driver-only, mock data, pre-finalized snapshot and offline start enforced).
6. Clean Android project that builds.

## Explicitly out of scope

- Any production API or backend code.
- Changes to the existing Python Visitor planner.
- Real authentication or real order source integration.
- Full warehouse/ERP integration unless separately approved.
