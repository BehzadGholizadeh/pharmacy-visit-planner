# Delivery Domain Model

## Entities & Relationships

~~~
DeliveryRoute 1 ────── * DeliveryStop
DeliveryRoute 1 ────── 1 DeliveryManifest (for the finalized route version)
DeliveryStop  1 ────── * Order
Order         1 ────── * OrderLine
DeliveryRoute 1 ────── * DeliveryEvent
DeliveryStop  1 ────── * DeliveryEvent
Order         1 ────── * DeliveryEvent
OrderLine     0..1 ─── * DeliveryEvent (when line-level quantity is recorded)
~~~

## Key Fields (conceptual)

### DeliveryRoute
- route_id (stable)
- version (integer; revisions are allowed only while the plan is still Draft)
- service_date (date in Asia/Tehran)
- assigned_driver_id
- status: Draft | Finalized | Assigned | Active | Completed
- finalized_at (timestamp on the previous day; freezes route and manifest)
- finalized_by
- published_at
- shift_started_at (nullable; records the driver's actual start and is distinct from route finalization)
- manifest_id
- manifest_version
- snapshot_checksum (recommended integrity check for the route + manifest snapshot)

### DeliveryStop
- stop_id
- route_id + route_version
- sequence (1-based; immutable after route finalization)
- pharmacy_gln / destination_id
- name, address snapshot
- lat, lon (optional)
- phone (optional – source still open)
- planned_arrival_estimate (optional)
- stop_outcome: Pending | Completed | Partial | Failed | Skipped

### DeliveryManifest
- manifest_id
- manifest_version
- route_id + route_version (must reference the exact finalized route version)
- service_date
- assigned_driver_id
- preparation_status: Pending | InPreparation | Prepared | Discrepancy
- published_to_warehouse_at
- prepared_at
- prepared_by
- immutable_after_finalization: true

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
- expected_qty_in_manifest
- loaded_qty (if actual loading confirmation is later approved)
- delivered_qty
- returned_qty (semantics and workflow remain open; do not use for generic undelivered quantities)

### DeliveryEvent (immutable)
- event_id (UUID, client-generated)
- route_id + route_version
- manifest_id + manifest_version
- stop_id / order_id / order_line_id (as applicable)
- event_type (including SHIFT_STARTED and delivery/preparation exception events)
- quantities (when relevant)
- reason_code (optional/required according to approved transition)
- note (optional)
- device_timestamp
- actor_id
- sync_status: Pending | Synced | Failed

## Invariants

- Route finalization occurs on the previous day for the service date.
- After finalized_at is set, route assignment, stop membership, stop sequence, order membership and manifest contents cannot be changed for that service date.
- The warehouse and driver app consume the same route_id/version and manifest_id/version.
- The driver may start offline only when the complete finalized route + manifest snapshot is already persisted locally for the correct driver and service date.
- shift_started_at records shift start; it does not create or move the immutability boundary.
- Every shift-start/delivery event references the finalized route and manifest versions.
- Delivery events and synchronization must never mutate the frozen route or manifest.
- Quantity invariants must be finalized with the approved delivery state model. Do not treat returned quantities as interchangeable with quantities that were never delivered.
