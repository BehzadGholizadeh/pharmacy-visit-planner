# Phase 1 Technical Decisions — Locked Before Slice 1

**Date:** 2026-10-30  
**Status:** Accepted implementation constraints  
**Applies to:** Native Android Driver app, package `com.pharmacyvisit.driver`

This document locks the R1–R9 review corrections and the three additional Product Owner clarifications.

## TD-01 — Manual dependency injection

- Use `AppContainer` / `DefaultAppContainer` and constructor injection.
- Use `ViewModelProvider.Factory` with `CreationExtras` for ViewModels, including SavedStateHandle support.
- Remove Hilt plugins, dependencies and annotations completely.
- Keep KSP aligned with Kotlin 2.0.21 for Room compiler code generation.

## TD-02 — Immutable snapshot vs. mutable warehouse and driver state

Immutable tables:
- `route_snapshots`
- `manifest_snapshots`
- `stop_snapshots`
- `order_snapshots`
- `order_line_snapshots`

`manifest_snapshots` stores only manifest identity/linkage fields: `manifestId`, `manifestVersion`, `routeId`, `routeVersion`, `serviceDate`, `assignedDriverId`, `publishedToWarehouseAt`.

`order_line_snapshots.expectedManifestQty` is frozen. It is not an actual prepared quantity.

Mutable pre-shift warehouse tables:
- `warehouse_preparation_state`: `manifestId`, `preparationStatus`, nullable `preparedAt`, nullable `preparedBy`.
- `warehouse_line_preparation_state`: `orderLineId`, actual `preparedQty`, update metadata.

Driver progress tables:
- `driver_session_state`
- `route_progress_state`
- `order_progress_state`
- `order_line_progress_state`
- `delivery_events_outbox`

The Snapshot DAO exposes read/initial-insert operations only. No post-finalization update/upsert/delete path may alter route, manifest, stop/order membership, sequence, assigned driver, ordered quantity or expected manifest quantity.

Warehouse preparation can be changed only before the associated route becomes `ACTIVE`. At ACTIVE, both preparation state and all warehouse line quantities are locked read-only for that service run.

## TD-03 — Tehran-local previous-day timestamp checks

Use `Instant` for event timestamps and an injectable `ClockProvider`. The business timezone is always `Asia/Tehran`.

For a new shift, all conditions must pass:
1. `serviceDate == LocalDate.now(tehranZone)`.
2. `finalizedAt.atZone(tehranZone).toLocalDate() < serviceDate`.
3. `downloadedAt.atZone(tehranZone).toLocalDate() < serviceDate`.
4. `downloadedAt >= finalizedAt`.

Null timestamps, wrong-day timestamps, download-before-finalization and a download on/after the service date block the new shift.

An already ACTIVE shift is recovered idempotently; it is not validated or executed as a second start, and it must not generate another `SHIFT_STARTED` event.

## TD-04 — Physically isolated operational and debug databases

- Operational database file: `driver_operational.db`.
- Debug/QA database file: `driver_debug_scenarios.db` (debug builds only; an isolated in-memory Room database is also acceptable for tests).
- Debug scenario reset may only operate on the debug database.
- Never seed, reset, clear or replace the operational database as a side effect of a scenario switch.
- A reset against a database containing an ACTIVE shift is blocked.
- Explicitly switching to the isolated debug database is permitted because it does not touch the operational shift or file.
- Release builds cannot select the debug profile.

## TD-05 — Quantities

For each order line:
- `orderedQty`: original ordered quantity.
- `expectedManifestQty`: frozen planned manifest quantity.
- `preparedQty`: actual quantity confirmed by warehouse.
- `deliveredQty`: actual quantity delivered.
- `remainingPreparedQty = preparedQty - deliveredQty`.
- `unfulfilledOrderQty = orderedQty - deliveredQty`.

Do not merge these quantities or name either result simply `remainingQty`.

## TD-06 — Stop roll-up and order outcome rules

Stop status is derived, with exclusive precedence:
1. All orders ready → PENDING.
2. Some terminal orders and at least one ready order → IN_PROGRESS.
3. No ready orders: all delivered → COMPLETED; all failed/refused → FAILED; otherwise → PARTIAL.

SKIPPED remains reserved and is not a Phase 1 driver action.

A Phase 1 order may transition once from READY_FOR_DELIVERY to a terminal outcome. DELIVERED requires all prepared quantities delivered; PARTIALLY_DELIVERED requires a positive delivered sum below prepared sum; FAILED/REFUSED require zero delivered quantity. Partial/failed/refused require a mock-only reason code.

## TD-07 — Event and progress transactionality

A new event UUID, its outbox row, and its corresponding progress projection update must commit atomically in one Room transaction. Duplicate event UUIDs return without re-applying progress. Persisted events are append-only in their business payload; sync metadata may progress through its outbox states.

## TD-08 — Durable recovery

Room is the durable source of truth for session, snapshot, warehouse preparation state, active shift, delivery progress and outbox. SavedStateHandle is only for navigation arguments and transient UI state.

## TD-09 — Debug fixtures

- Default fixture insertion is idempotent and occurs only when the selected database is empty.
- Debug-only scenario controls are inaccessible in release and normal driver flow.
- Scenario fixtures never bypass the offline-start guard.
- Scenario switching/reset never erases the operational DB or its active shift.

## Implementation order

Slice 1: Manual DI, Gradle/dependency foundation, domain enums/models and Tehran ClockProvider.  
Slice 2: Room snapshot/preparation/progress/outbox schemas, isolated database profiles, DAOs and idempotent seed.  
Slice 3: repository/use cases, temporal offline-start validation, ACTIVE recovery, immutability and atomic event/progress operations.  
Slice 4: Compose screens, ViewModels, navigation and debug-only QA controls.  
Slice 5: T-01 through T-11 acceptance tests.

No production API/ERP integration or Python Visitor planner changes are authorized by these technical decisions.
