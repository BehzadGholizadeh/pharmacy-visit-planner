# State Machines — Phase 1 (Accepted for Mock)

The domain uses separate state machines for the immutable route snapshot, mutable warehouse preparation, and driver operational progress.

## Route snapshot status

```
Draft → Finalized → Assigned
```

- `FINALIZED` is the previous-day immutability boundary.
- Driver assignment is frozen with the finalized snapshot. `ASSIGNED` is an eligible snapshot status, not permission to reassign or mutate it.
- No stop/order membership, sequence, driver, expected manifest quantity, or version replacement is allowed after finalization for that service date.

## Route operational progress

```
READY_TO_START → ACTIVE → COMPLETED
```

- `ACTIVE` means the driver has started the shift and `shiftStartedAt` is persisted.
- Recovering an existing `ACTIVE` route restores the existing shift timestamp and does not emit another `SHIFT_STARTED` event.
- `COMPLETED` routes cannot be restarted.

## Manifest snapshot

The identity/version and route linkage are immutable:

- `manifestId`
- `manifestVersion`
- `routeId`
- `routeVersion`
- `serviceDate`
- `assignedDriverId`
- `publishedToWarehouseAt`

Preparation status and actual prepared quantities are **not** fields in this snapshot.

## Warehouse preparation state

```
PENDING → IN_PREPARATION → PREPARED
                       ↘ DISCREPANCY
```

- Preparation state lives in `warehouse_preparation_state`; actual line quantities live in `warehouse_line_preparation_state`.
- The driver cannot start before the state is `PREPARED` and line data passes validation.
- Preparation is mutable only before the route becomes `ACTIVE`.
- As soon as the route is `ACTIVE`, manifest-level preparation and line-level prepared quantities are read-only for that service run.

## Stop status (derived from order outcomes)

Precedence is exclusive:

1. All orders are `READY_FOR_DELIVERY` → `PENDING`.
2. At least one order has a terminal outcome and at least one remains `READY_FOR_DELIVERY` → `IN_PROGRESS`.
3. No order remains ready:
   - all `DELIVERED` → `COMPLETED`;
   - all `FAILED` or `REFUSED` → `FAILED`;
   - any `PARTIALLY_DELIVERED`, or a mix of `DELIVERED` with `FAILED`/`REFUSED` → `PARTIAL`.

`SKIPPED` is reserved in the domain enum but is not a driver action in Phase 1. A stop cannot be terminal while any order remains unresolved.

## Order status

```
READY_FOR_DELIVERY → DELIVERED
                   → PARTIALLY_DELIVERED
                   → FAILED
                   → REFUSED
```

- Phase 1 allows one final outcome transition per order. A terminal outcome cannot be overwritten.
- `DELIVERED`: every order line has `deliveredQty == preparedQty`.
- `PARTIALLY_DELIVERED`: sum of delivered quantities is greater than zero and less than sum of prepared quantities.
- `FAILED`/`REFUSED`: delivered quantities are zero on every order line.
- Partial, failed and refused outcomes require a mock reason code in Phase 1.
- Returned/physical return-to-warehouse is deferred. Cancellation after finalization must not mutate route or manifest snapshots.

## Order-line quantities

- `orderedQty`: customer order quantity (snapshot).
- `expectedManifestQty`: planned manifest quantity (snapshot).
- `preparedQty`: actual warehouse quantity (preparation state).
- `deliveredQty`: actual delivered quantity (progress state).
- `remainingPreparedQty = preparedQty - deliveredQty`.
- `unfulfilledOrderQty = orderedQty - deliveredQty`.

The two derived quantities must not be conflated.
