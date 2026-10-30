# Delivery Domain Model — Phase 1

This model separates the frozen previous-day delivery snapshot from mutable operational progress. The separation is mandatory; progress updates must never rewrite finalized route or manifest facts.

## 1. Immutable previous-day snapshot

The following data is persisted from the finalized route/manifest download and is read-only for the service run:

- **RouteSnapshot** (`route_snapshots`): `routeId`, `routeVersion`, `serviceDate`, `timezone`, `assignedDriverId`, `snapshotStatus`, `publishedAt`, `finalizedAt`, `finalizedBy`, local `downloadedAt`, `snapshotChecksum`, `snapshotComplete`.
- **ManifestSnapshot** (`manifest_snapshots`): `manifestId`, `manifestVersion`, `routeId`, `routeVersion`, `serviceDate`, `assignedDriverId`, `publishedToWarehouseAt`.
- **StopSnapshot** (`stop_snapshots`): `stopId`, `routeId`, immutable `sequence`, pharmacy name/address/coordinates and optional phone.
- **OrderSnapshot** (`order_snapshots`): `orderId`, `stopId`, `routeId`, initial readiness status (`READY_FOR_DELIVERY`).
- **OrderLineSnapshot** (`order_line_snapshots`): `orderLineId`, `orderId`, SKU/product facts, `orderedQty` and immutable `expectedManifestQty`.

The expected manifest quantity is the planned quantity captured in the frozen manifest. It is not the actual warehouse-prepared quantity.

## 2. Mutable warehouse preparation — separate from the snapshot

Preparation has its own lifecycle and tables. It is not a mutable column on `manifest_snapshots`.

- **WarehousePreparationState** (`warehouse_preparation_state`): `manifestId`, `preparationStatus` (`PENDING`, `IN_PREPARATION`, `PREPARED`, `DISCREPANCY`), nullable `preparedAt`, nullable `preparedBy`.
- **WarehouseLinePreparationState** (`warehouse_line_preparation_state`): `orderLineId`, actual `preparedQty`, and update metadata.

Before the driver starts the shift, warehouse preparation can progress and actual prepared quantities can be recorded against the expected manifest quantities. The driver cannot start until the preparation state is `PREPARED` and its line-level data is complete and valid.

**Preparation lock:** once the associated route becomes operationally `ACTIVE`, both the manifest-level preparation state and all warehouse line quantities become read-only for that service run. No warehouse preparation edit may mutate the active run.

## 3. Mutable operational progress

- **DriverSessionState** (`driver_session_state`): current authenticated local driver session.
- **RouteProgressState** (`route_progress_state`): `routeId`, `routeVersion`, operational status (`READY_TO_START`, `ACTIVE`, `COMPLETED`), `shiftStartedAt`, `shiftCompletedAt`.
- **OrderProgressState** (`order_progress_state`): current delivery status, reason/note and the event that recorded the outcome.
- **OrderLineProgressState** (`order_line_progress_state`): delivered quantity and event reference.
- **DeliveryEvent** (`delivery_events_outbox`): append-only client UUID event with exact route/manifest IDs and versions, actor, device time and sync status. Outbox sync metadata may change; event identity and business payload do not.

The database profile is selected by the application container:
- `driver_operational.db` for operational app data.
- `driver_debug_scenarios.db` for debug/QA fixtures only.

A debug scenario reset must not access or erase the operational database. A reset against a database containing an ACTIVE shift is blocked. Only switching to the physically isolated debug database permits scenario reset while an operational shift exists.

## 4. Quantity semantics

For each order line:

- `orderedQty`: quantity requested by the pharmacy.
- `expectedManifestQty`: quantity planned in the immutable manifest.
- `preparedQty`: actual quantity confirmed by warehouse, stored in `warehouse_line_preparation_state`.
- `deliveredQty`: quantity delivered by the driver, stored in `order_line_progress_state`.
- `remainingPreparedQty = preparedQty - deliveredQty`: still deliverable from today's prepared shipment.
- `unfulfilledOrderQty = orderedQty - deliveredQty`: total original customer order quantity still unfulfilled.

Do not use a generic `remainingQty` for both meanings.

## 5. Offline-start temporal invariants

For a new shift start, all dates are evaluated using `Asia/Tehran`:

1. `route.serviceDate == LocalDate.now(tehranZone)`.
2. `route.finalizedAt.atZone(tehranZone).toLocalDate() < route.serviceDate`.
3. `route.downloadedAt.atZone(tehranZone).toLocalDate() < route.serviceDate`.
4. `route.downloadedAt >= route.finalizedAt`.

A download after the start of the service date, before finalization, or without the previous-day finalized snapshot blocks a new offline start. A previously ACTIVE shift is recovered idempotently; it is not treated as a new start.

The route must be assigned to the authenticated local driver, the matching manifest must be PREPARED, all route/manifest identity and version references must match, all stops/orders/lines must be complete, and local checksum validation must succeed.

A local checksum in Phase 1 detects accidental corruption only. Production authenticity requires server-side signing/verification under D-17.

## 6. Persistence invariants

1. Snapshot tables have insert/read behavior only after initial persistence; no update/upsert/delete path may change finalized route, manifest, stop/order membership, sequence, expected quantities, or assigned driver.
2. Warehouse preparation can change only before the associated route becomes ACTIVE.
3. Delivery progress is written only to progress tables.
4. Every event references the exact route ID/version and manifest ID/version.
5. Event insertion and progress projection updates are atomic and idempotent in one Room transaction.
6. Room is the durable source of truth after process death. `SavedStateHandle` is for navigation/transient UI state only.
