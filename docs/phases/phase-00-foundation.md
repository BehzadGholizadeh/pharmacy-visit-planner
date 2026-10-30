# Phase 0 – Product & Integration Foundation

**Goal:** Close all critical product and architecture decisions so that Phase 1 (Driver MVP with mock data) can be implemented safely.

## Exit Criteria (must all be true)

- [ ] Decision Register items D-06, D-08–D-15 have explicit Product Owner decisions or accepted recommendations.
- [ ] Delivery domain model and state machines are approved.
- [ ] Example JSON data contract is approved (or marked as “good enough for mock”).
- [ ] Route lock / no mid-day change rule is reflected in all active documents.
- [ ] Android build configuration (Kotlin + Compose) is verified and Gradle wrapper is present.
- [ ] PRD v1.1, domain model, data-contract examples and phase-01 prompt are consistent.
- [ ] No contradictory Visitor-centric language remains in active Driver documents (or is clearly marked superseded).

## Deliverables of this phase

1. Approved Decision Register.
2. `driver-delivery-prd-v1.1.md`
3. Domain model + state machines + JSON examples.
4. Updated Phase 1 prompt for Gemini (Driver-only, mock data, route lock enforced).
5. Clean Android project that builds.

## Explicitly out of scope

- Any production API or backend code.
- Changes to the existing Python Visitor planner.
- Real authentication or real order source integration.
