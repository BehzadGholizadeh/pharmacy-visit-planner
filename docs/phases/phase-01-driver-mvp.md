# Phase 1 – Driver MVP (Controlled Mock Data)

**Prerequisite:** Phase 0 exit criteria met.

## Goal

A fully usable Driver experience on device using realistic **mock** data, with the same day-before preparation pattern expected in operations:

- A finalized route and matching warehouse manifest are created for the next service date on the previous day.
- Warehouse preparation status is represented in mock data and tied to the exact route/manifest version.
- The driver's device downloads and persists the complete finalized route + manifest on the previous day.
- On the service date, the driver can start the shift online or offline from that local snapshot.
- If the local snapshot is missing, incomplete, corrupt, assigned to another driver/date, or route/manifest versions do not match, shift start is blocked.
- Start Shift records the operational start; it does not lock an editable route. The route was already immutable from previous-day finalization.
- Ordered stop list + next-stop focus.
- Stop detail with multiple orders and order lines.
- Record Delivered / Partially Delivered / Failed / Refused (with quantities and reasons according to the mock-approved state model).
- Local persistence (Room) + event outbox.
- External navigation handoff.
- End-of-day summary and pending sync state.
- Tests that prove the finalized route and manifest cannot change after finalization and that offline start works only with a complete matching snapshot.

## Gemini Prompt Guidance

Always instruct Gemini:

> Work only on the Driver delivery flow.  
> Do not implement Visitor features.  
> Do not implement a production API, ERP integration or real authentication in this phase.  
> Use realistic mock data that represents a route and warehouse manifest finalized on the previous day.  
> Persist the route and matching manifest locally before the service date.  
> On the service date, allow Start Shift offline only if the exact finalized snapshot exists locally, is complete, matches the logged-in mock driver and service date, and has matching route/manifest versions.  
> If required local data is missing or mismatched, block shift start with a clear actionable message.  
> After finalization, do not allow any code path to edit the route, assigned driver, stop membership, stop order, order membership or manifest contents.  
> Shift start must not be treated as the moment when route immutability begins.  
> Delivery events must reference the finalized route and manifest IDs/versions and be persisted locally before UI success feedback.  
> Use the domain model and JSON examples in docs/architecture/.  
> Prefer the smallest possible changes. Do not rewrite existing files unnecessarily.

## Definition of Done

- App builds and runs on emulator/device.
- Mock next-day route and matching warehouse manifest can be prepared and downloaded the previous day.
- Warehouse preparation status is visible and tied to the exact manifest version.
- Tester can close/reopen the app and see the preloaded snapshot.
- Tester can switch the app/device to airplane mode and start the shift using the preloaded route and manifest.
- Tester can complete a simulated day (including partial and failed deliveries) while offline.
- Every event remains queued locally and synchronizes once when connectivity returns (mock sync is acceptable in this phase).
- Missing/mismatched/corrupt local route or manifest blocks offline start.
- No route or manifest mutation is possible after previous-day finalization (enforced by unit/UI tests).
