# Gemini Phase 1 Architecture & Implementation Plan — Review

**Date:** 2026-10-30  
**Reviewer:** ChatGPT  
**Scope:** Review of the Product Owner-provided Gemini planning response against the current `main` branch, the approved Decision Register, PRD v1.1, domain model, state machines, data contract, and Android starter scaffold.

## 1. Overall verdict

**APPROVE WITH REQUIRED CORRECTIONS — planning is strong, but implementation should not start from this plan unchanged.**

The plan correctly identifies the starter project's current limitations and proposes a sensible offline-first architecture for Phase 1. Its main decisions are compatible with the approved product scope. However, several details are either internally inconsistent or insufficiently specified to guarantee the product's core invariants.

This review records implementation guidance. It does **not** authorize changes to production integrations, the Python Visitor planner, or any deferred product behavior.

## 2. What is correct and accepted

1. **Starter-project assessment:** The inspected scaffold is a UI-only baseline. The current `DriverNavHost` navigates to `stop/$stopId` without registering a stop-detail destination. There is no Room/domain/repository implementation yet. This matches the plan's assessment.
2. **Manual dependency injection:** `AppContainer` + constructor injection + `ViewModelProvider.Factory` is a reasonable choice for this single-module AI Studio project. Hilt is not a product requirement.
3. **Canonical Kotlin enums:** Using explicit Kotlin enum values and mapping external JSON strings at the data boundary is preferable to spreading raw strings throughout the application.
4. **Offline-first local storage:** Room, a deterministic local mock repository, a persisted event outbox, and a Tehran-aware clock are appropriate for the approved Phase 1 scope.
5. **Scope discipline:** No ERP/API integration, production authentication, live location, production proof-of-delivery, warehouse scanning, or Visitor features should be implemented in Phase 1.
6. **Testing focus:** Offline-start validation, immutable route behavior, partial delivery, and recovery after process recreation are the right high-risk areas to test.

## 3. Required corrections before implementation

### R1. Complete the Manual DI migration; retain KSP for Room

The current starter scaffold still uses Hilt:
- `DriverApp.kt` has `@HiltAndroidApp`.
- `MainActivity.kt` has `@AndroidEntryPoint`.
- Root and app Gradle files apply the Hilt plugin and include Hilt dependencies.

If Manual DI is selected, remove those Hilt annotations, plugins, and dependencies consistently, then initialize one `AppContainer` from `DriverApp`. Do not leave a half-Hilt / half-manual configuration.

**Important:** KSP is still required when Room's compiler is configured through KSP. Manual DI removes the need for Hilt/KSP processing, not Room/KSP processing. Keep the KSP plugin version aligned with Kotlin 2.0.21.

The existing GitHub prompt `docs/phases/gemini-phase-01-prompt.md` still mandates Hilt. It must be revised to match the accepted Manual DI architecture before it is reused.

### R2. Separate the immutable delivery snapshot from delivery progress

Do not update finalized route/manifest snapshot rows to record delivery progress.

Treat these as immutable snapshot data after finalization:
- route identity, version, service date, assigned driver and finalized timestamp;
- manifest identity/version/status and its prepared quantities;
- stop membership and sequence;
- order membership and ordered/prepared quantities.

Store mutable operational progress separately, for example in delivery-progress/projection tables keyed by the immutable snapshot IDs. This includes delivered quantities, current order/stop outcomes, and shift progress.

A DAO/repository may update progress, but it must not expose a command that changes the finalized snapshot. Enforce this boundary in repository/domain operations and database design—not only by convention or UI disabling.

### R3. Make offline-start validation exhaustive and recovery idempotent

The plan's six listed test conditions are not enough to cover D-16/D-17. Validate all of the following before a new shift starts:

- route exists locally and is in an eligible finalized state (`FINALIZED` or `ASSIGNED`);
- route is assigned to the current local driver session;
- route service date is today's date in `Asia/Tehran`;
- finalized route and its snapshot were persisted locally from the previous-day download;
- matching manifest exists and is `PREPARED`;
- manifest `routeId`, `routeVersion`, `serviceDate`, and `assignedDriverId` match the route;
- local snapshot metadata matches the same route ID/version and manifest ID/version;
- all required stops, orders, lines and quantities are present and valid;
- local integrity/checksum validation succeeds.

If the route is already `ACTIVE`, this is **recovery of an existing shift**, not a new shift start. Restore the existing `shiftStartedAt` and state; do not create a second `SHIFT_STARTED` event or reset the timestamp. A completed route must not be restarted.

A local checksum is an accidental-corruption check for this mock phase; it is not proof of authenticity or protection against a maliciously modified device. Production authenticity remains a server-signing concern under D-17.

### R4. Resolve quantity semantics explicitly

The current plan uses:

`remainingQty = orderedQty - deliveredQty`

That is the quantity still unfulfilled against the customer's original order. It is not necessarily the quantity still deliverable from this day's prepared manifest.

For the current delivery, use an unambiguous derived value:

`remainingPreparedQty = preparedQty - deliveredQty`

If the product also needs the customer's total outstanding quantity, expose it separately as:

`unfulfilledOrderQty = orderedQty - deliveredQty`

Do not use one ambiguous `remainingQty` for both meanings.

Also define the boundary mapping for `expected_qty_in_manifest` in the existing JSON example. Map it to `preparedQty` only when it represents the quantity actually confirmed as prepared. If it is merely a planned target, keep it distinct from actual `preparedQty`. A manifest marked `PREPARED` must have a clear, consistent meaning.

### R5. Fix the multi-order StopStatus roll-up precedence

The proposed rules overlap. For example, one order can be partially delivered while a sibling order is still `READY_FOR_DELIVERY`; the plan could label the stop both `IN_PROGRESS` and `PARTIAL`.

Use an explicit precedence:

1. If all orders are still ready and untouched → `PENDING`.
2. If at least one order has an outcome but one or more orders remain ready → `IN_PROGRESS`.
3. Once every order has a terminal outcome:
   - all `DELIVERED` → `COMPLETED`;
   - all `FAILED`/`REFUSED` → `FAILED`;
   - any partial outcome or a mixture of delivered and failed/refused → `PARTIAL`.

Define whether `SKIPPED` is a user action or only a derived operational state. If it is actionable, specify its reason and how its orders are treated; otherwise keep it out of the Phase 1 UI and leave the state unused. Do not let a stop become terminal while it still contains unresolved orders.

### R6. Make order-outcome transitions safe

The proposed quantity rules are a good baseline:
- each line: `0 <= deliveredQty <= preparedQty`;
- `PARTIALLY_DELIVERED`: total delivered quantity is greater than zero and less than total prepared quantity;
- `FAILED`/`REFUSED`: no quantities delivered;
- partial, failed and refused outcomes require a reason.

Add two safeguards:
- `DELIVERED` must mean all prepared quantities for the order were delivered.
- In Phase 1, treat an outcome submission as one final outcome per order. Do not allow a later `FAILED`/`REFUSED` action to reset quantities already delivered by an earlier partial event. An outcome-correction workflow is not defined and must not be invented.

Reason codes are required by the decision, but the approved documents do not define a production reason-code catalogue. Any Phase 1 values must be clearly labelled as a mock-only set, with a generic/other path if needed; do not present them as approved production policy.

### R7. Make event-first persistence atomic and idempotent

Persist the event and update the local progress projection in one Room transaction:
1. insert the client-generated event UUID;
2. apply the corresponding progress update;
3. commit both together.

If the event UUID already exists, do not apply its progress update a second time. A crash must not leave a committed projection without its event, or an event that is applied twice. Add duplicate-event and transaction-rollback tests.

### R8. Treat Room as the source of truth after process death

Room must own the durable route snapshot, local driver session, shift timestamp, delivery progress, and pending outbox events.

Use `SavedStateHandle` for navigation arguments and small transient UI state only; it is not a replacement for durable business persistence. Recovery tests should close/recreate the repository and ViewModels against the same persisted database and verify that the exact active snapshot and event outbox return. Add a separate on-device relaunch/force-stop acceptance check.

### R9. Keep QA scenario switching out of the normal driver workflow

The proposed Mock Scenario Switcher is useful for QA, but it must be debug/test-only (or otherwise inaccessible in the normal driver experience). It must select invalid fixtures for validation tests without editing the finalized snapshot or providing a way to bypass the start guard.

Seed data should be deterministic and idempotent: app relaunch must not recreate/replace the route or erase delivery progress. The demo fixture should represent a snapshot downloaded on the previous day for the current `Asia/Tehran` service date; tests should inject a fixed clock.

## 4. Architecture refinements recommended

- Put the repository contract in the domain layer (for example, `domain/repository/DriverRepository`) and its Room implementation in the data layer (for example, `data/repository/RoomDriverRepository`).
- Add an explicit `EndOfDaySummaryViewModel`; derive the summary from persisted Room state, not screen-local calculations.
- Add lifecycle Compose dependencies needed for lifecycle-aware state collection, plus `kotlinx-coroutines-test` and `room-testing` if used by the selected test strategy.
- Keep the Google Maps/Neshan/Waze handoff behind a small navigation-intent helper. Use an Android chooser/fallback and support address-only stops; do not make the core delivery flow depend on one installed map package.
- Build in vertical slices with a compile/test checkpoint after each slice rather than generating every file in one large pass.

## 5. Minimum acceptance tests to add

1. Route missing, not finalized, wrong date, wrong driver, or not previously downloaded → shift start blocked.
2. Manifest missing, not Prepared, wrong ID/version/date/driver, or snapshot checksum mismatch → shift start blocked.
3. Empty/incomplete/corrupt stop/order/line data or invalid quantities → shift start blocked.
4. Valid finalized + Prepared snapshot for today's Tehran date and the matching driver → shift starts and persists one `SHIFT_STARTED` event.
5. Existing `ACTIVE` route → resume existing shift without a second start event or timestamp reset.
6. All attempts to alter finalized route membership, assignment, stop sequence, order data or manifest quantities are rejected; progress updates remain allowed only in separate progress storage.
7. Quantity boundaries, Delivered/Partial/Failed/Refused semantics, mandatory reasons and duplicate submissions are tested.
8. Multi-order stop roll-up covers untouched, mixed pending/resolved, all delivered, all failed/refused, and mixed terminal outcomes.
9. Event insertion + progress update are atomic and idempotent under duplicate UUID and simulated failure.
10. Reopening the app against the same database restores session, active route, stop/order progress and pending outbox events.
11. End-of-day unresolved orders become `Pending Manager Review` without auto-carryover or route/manifest mutation.

## 6. Implementation authorization

The Gemini plan is accepted as the **basis for the Phase 1 design**, subject to R1–R9 above being incorporated into the plan/prompt.

Before coding:
- update the AI Studio-specific implementation prompt to use Manual DI and remove Hilt references;
- reconcile the quantity and stop-roll-up rules;
- explicitly specify the immutable snapshot/progress data boundary and idempotent ACTIVE recovery.

Then implement in small, buildable increments. Keep the Phase 1 mock boundary intact. Do not modify the Python Visitor planner or introduce production integrations.

**Final status:** Planning review complete; implementation is **not yet authorized from the uncorrected plan**.
