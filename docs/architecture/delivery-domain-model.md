# Delivery Domain Model

## Entities & Relationships

```
DeliveryRoute 1 ────── * DeliveryStop
DeliveryStop  1 ────── * Order
Order         1 ────── * OrderLine
DeliveryRoute 1 ────── * DeliveryEvent
DeliveryStop  1 ────── * DeliveryEvent
Order         1 ────── * DeliveryEvent
OrderLine     0..1 ─── * DeliveryEvent   (when line-level quantity is recorded)
```

## Key Fields (conceptual)

### DeliveryRoute
- route_id (stable)
- version (integer, increments on republish)
- service_date (date in Asia/Tehran)
- assigned_driver_id
- status: Draft | Published | Assigned | Active | Completed | Cancelled | Superseded
- locked_at (nullable timestamp – set at shift start)
- published_at

### DeliveryStop
- stop_id
- route_id + version
- sequence (1-based, immutable after lock)
- pharmacy_gln / destination_id
- name, address snapshot
- lat, lon (optional)
- phone (optional – source still open)
- planned_arrival_estimate (optional)
- stop_outcome: Pending | Completed | Partial | Failed | Skipped

### Order
- order_id (authoritative business ID)
- stop_id
- readiness_status
- delivery_status: Pending | Loaded | Delivered | PartiallyDelivered | Failed | Refused | Returned | Cancelled

### OrderLine
- order_line_id
- order_id
- sku / product_name
- ordered_qty
- loaded_qty
- delivered_qty
- returned_qty

### DeliveryEvent (immutable)
- event_id (UUID, client-generated)
- route_id + version
- stop_id / order_id / order_line_id (as applicable)
- event_type
- quantities (when relevant)
- reason_code (optional)
- note (optional)
- device_timestamp
- actor_id
- sync_status: Pending | Synced | Failed

## Invariants

- After `locked_at` is set, sequence and membership of stops must not change.
- Every DeliveryEvent created after lock must reference the locked route_id + version.
- Quantities on OrderLine must satisfy: delivered_qty + returned_qty ≤ loaded_qty ≤ ordered_qty (or explicit business rules once approved).
