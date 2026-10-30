# Google AI Studio — Native Android Driver App — Phase 1 Implementation Prompt

**Project root:** `android/`  
**Application ID / namespace:** `com.pharmacyvisit.driver`  
**Target environment:** Google AI Studio → Build → Android (native Kotlin / Jetpack Compose)

The repository already contains the Slice 1 foundation: Manual DI, Kotlin domain models, the Tehran ClockProvider, and Room/KSP dependency setup. Inspect the current project and continue from that state; do not recreate or duplicate Slice 1.

## Source of truth

Read these files before coding:
- `docs/product/decision-register.md`
- `docs/product/driver-delivery-prd-v1.1.md`
- `docs/architecture/phase-1-technical-decisions.md`
- `docs/architecture/delivery-domain-model.md`
- `docs/architecture/state-machines.md`
- `docs/architecture/data-contract-examples.md`
- `docs/reviews/gemini-phase-01-plan-review-2026-10-30.md`

If a conflict appears, do not invent a product rule. Report it before proceeding.

## Non-negotiable scope

1. Implement ONLY the Driver delivery workflow. Do not add Visitor features.
2. Do not edit, reuse or rewrite the existing Python Visitor planner.
3. Phase 1 is deterministic local mock data only: no ERP, production API, real authentication, photo/signature/OTP/GPS proof, warehouse scanning or live location.
4. The route and manifest snapshot is finalized on the previous day and immutable thereafter.
5. Warehouse preparation is separate mutable state before shift start. Once the route is ACTIVE, preparation state and line quantities are read-only.
6. The driver can start offline only from the exact, complete, locally persisted, finalized route and matching PREPARED manifest assigned to the authenticated driver for today's Asia/Tehran service date.
7. An ACTIVE shift is recovered idempotently with the same timestamp and no duplicate SHIFT_STARTED event. COMPLETED cannot restart.
8. Do not mutate finalized snapshot data to represent delivery progress.

## Architecture and build constraints

- Kotlin 2.0.21, Jetpack Compose, Material 3, single Activity/single app module.
- Manual constructor DI through `AppContainer` / `DefaultAppContainer`.
- Use `ViewModelProvider.Factory` with `CreationExtras`; use SavedStateHandle only for navigation/transient UI state.
- Hilt is forbidden: do not add its plugins, annotations or dependencies.
- Keep KSP 2.0.21-1.0.25 for Room code generation.
- Room is the durable source of truth.
- Use the injectable `ClockProvider` and `Asia/Tehran`; never rely on the device's default timezone.
- Keep builds small and compilable after every vertical slice.

## Storage contract

### Immutable snapshot tables
- `route_snapshots`
- `manifest_snapshots`
- `stop_snapshots`
- `order_snapshots`
- `order_line_snapshots`

Manifest snapshot stores only identity/linkage: `manifestId`, `manifestVersion`, `routeId`, `routeVersion`, `serviceDate`, `assignedDriverId`, `publishedToWarehouseAt`.

Order line snapshot stores `orderedQty` and `expectedManifestQty`; it does not store actual prepared or delivered quantities.

Snapshot DAO must not provide update/upsert/delete operations that can alter finalized route/manifest/stop/order membership, stop sequence, assignment, ordered quantities or expected manifest quantities.

### Separate warehouse preparation tables
- `warehouse_preparation_state`: manifest ID, preparation status (PENDING / IN_PREPARATION / PREPARED / DISCREPANCY), preparedAt, preparedBy.
- `warehouse_line_preparation_state`: orderLineId and actual preparedQty.

Preparation can change before shift start. As soon as route operational status becomes ACTIVE, both tables are read-only for that route/service run. Start requires PREPARED plus complete and valid line quantities.

### Mutable driver progress/outbox tables
- `driver_session_state`
- `route_progress_state`
- `order_progress_state`
- `order_line_progress_state`
- `delivery_events_outbox`

Operational progress must never mutate snapshot records.

### Database isolation
- Operational file: `driver_operational.db`.
- Debug QA file: `driver_debug_scenarios.db` (debug only; isolated in-memory Room is acceptable for tests).
- Debug reset/seed acts only on the debug database. It must never clear or overwrite operational data.
- A reset against the currently selected database is blocked if it contains an ACTIVE shift. Switching explicitly to the physically isolated debug database is safe and does not touch the operational shift.
- Release cannot select the debug profile.

## Offline-start temporal rules

For a new shift:
1. route serviceDate equals today's date in Asia/Tehran;
2. finalizedAt's Tehran-local date is before serviceDate;
3. downloadedAt's Tehran-local date is before serviceDate;
4. downloadedAt is greater than or equal to finalizedAt;
5. route is FINALIZED or ASSIGNED and assigned to the current authenticated driver;
6. manifest exists, is PREPARED, and its route ID/version, service date and driver match the route;
7. local snapshot metadata matches both route and manifest identities/versions and snapshotComplete is true;
8. stops/orders/lines exist, sequences are contiguous, orderedQty > 0 and 0 < preparedQty <= expectedManifestQty (or a documented shortage/discrepancy state that blocks shift start);
9. checksum/integrity verification succeeds.

Any failure blocks start with a clear Persian message and a stable reason code. A local checksum detects accidental corruption only; it is not production authenticity. If the route is already ACTIVE, resume it without emitting another SHIFT_STARTED event or resetting shiftStartedAt. COMPLETED cannot restart.

## Quantity and outcome rules

- `remainingPreparedQty = preparedQty - deliveredQty`.
- `unfulfilledOrderQty = orderedQty - deliveredQty`.
- Do not use an ambiguous remainingQty.
- Each line: 0 <= deliveredQty <= preparedQty.
- DELIVERED means every line deliveredQty == preparedQty.
- PARTIALLY_DELIVERED means total delivered > 0 and < total prepared; reason required.
- FAILED / REFUSED means all deliveredQty values are zero; reason required.
- Phase 1 permits one final outcome per order from READY_FOR_DELIVERY. Reject outcome overwrites.
- Mock reason catalogue: CUSTOMER_UNAVAILABLE, CUSTOMER_REFUSED_ORDER, PARTIAL_ACCEPTANCE_BY_PHARMACY, DAMAGED_OR_DISCREPANCY_AT_HANDOFF, OTHER (note required). Label it mock-only.

## Stop-status roll-up

Apply this exclusive precedence:
1. all orders READY_FOR_DELIVERY → PENDING;
2. at least one terminal order and at least one READY_FOR_DELIVERY → IN_PROGRESS;
3. no orders remain ready: all DELIVERED → COMPLETED; all FAILED/REFUSED → FAILED; otherwise → PARTIAL.

SKIPPED is reserved and must not appear as a Phase 1 driver action.

## Atomic/idempotent events

Every shift/outcome command runs in one Room transaction:
1. check event UUID; if already present, return without applying progress again;
2. insert the immutable event business payload into the outbox;
3. update the corresponding progress projection.

Rollback the entire transaction if any step fails. Duplicate UUID and rollback behavior must be tested. Sync status may change; event identity/business facts may not.

## Phase implementation sequence

### Slice 1 — already present in the repository
Inspect and preserve Manual DI, domain enums/models, ClockProvider, Compose/Kotlin plugin, KSP and Room dependencies. Do not redo it unless a defect is found; report any defect.

### Slice 2 — Room persistence
Implement entities/DAOs/database for all snapshot, warehouse preparation, progress and outbox tables. Physically isolate operational/debug files. Implement snapshot insert-if-absent only, no snapshot mutation API. Seed deterministic fixture only when the selected DB is empty. Add Room schema export/migration baseline and DAO transaction tests.

### Slice 3 — Domain/repository/use cases
Implement domain repository contract and Room repository. Implement temporal offline-start guard, ACTIVE recovery, route/snapshot immutability rules, warehouse preparation lock, stop roll-up, order outcome validation, atomic/idempotent event handling and debug database guard. Add unit tests.

### Slice 4 — UI
Implement mock login, pre-shift status, route list/next stop, stop detail with multiple orders/lines and quantity controls, reasons, end-of-day summary, navigation, and debug-only isolated scenario controls. Persian-first RTL, Material 3 and large touch targets. External map handoff must support address-only fallback and must not block delivery flow.

### Slice 5 — acceptance tests
Implement all T-01 through T-11 from the architecture review/technical decisions. Include process recreation using the same Room database and a separate device relaunch/force-stop check.

## Working protocol

- Before each slice, list the exact files to create/change and the acceptance criteria.
- Implement one vertical slice at a time.
- After each slice, run available compile/tests and report exact commands/results. Do not claim a build succeeded unless it was actually run.
- Do not proceed past a failing build or unresolved product contradiction.
- Preserve existing unrelated files; do not rewrite the app wholesale.
- Do not modify the Python Visitor planner.
