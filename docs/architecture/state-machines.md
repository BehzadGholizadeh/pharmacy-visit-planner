# State Machines – Phase 1 (Accepted for Mock)

## Route
```
Draft → Finalized → Assigned → Active → Completed
```
- Finalized = previous-day freeze (immutable thereafter).
- Active = driver has started the shift (`shift_started_at` set).
- No transitions that alter stops/orders/sequence after Finalized.

## Manifest
```
Pending → InPreparation → Prepared
                       ↘ Discrepancy
```
- Phase 1 requires status **Prepared** before shift start is allowed.

## Stop
```
Pending → InProgress → Completed
                    → Partial
                    → Failed
                    → Skipped
```

## Order
```
ReadyForDelivery → Delivered
                → PartiallyDelivered
                → Failed
                → Refused
```
- Failed, Refused and PartiallyDelivered require a reason.
- Returned / physical return-to-warehouse deferred.
- Cancellation after finalization does not mutate route or manifest.

## OrderLine quantities
- ordered_qty
- prepared_qty
- delivered_qty
- remaining_qty = ordered_qty - delivered_qty (derived)
