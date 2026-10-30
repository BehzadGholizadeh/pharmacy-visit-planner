# Delivery Domain Model (Phase 1)

## Core entities

- **DeliveryRoute**: route_id, version, service_date, assigned_driver_id, status, finalized_at, shift_started_at, manifest_id, manifest_version
- **DeliveryManifest**: manifest_id, version, route_id, route_version, status (Prepared required for start)
- **DeliveryStop**: stop_id, sequence (immutable after finalization), pharmacy snapshot, phone (optional), orders
- **Order**: order_id, stop_id, status
- **OrderLine**: order_line_id, sku, product_name, ordered_qty, prepared_qty, delivered_qty
- **DeliveryEvent**: event_id (UUID), route_id+version, manifest_id+version, stop/order/line refs, event_type, quantities, reason, note, device_timestamp, sync_status

## Key invariants

1. After `finalized_at` the route + manifest snapshot is immutable.
2. Shift start only sets `shift_started_at`; it does not create the freeze.
3. Every event references the exact route_id/version + manifest_id/version.
4. Offline start requires local presence of the exact Finalized + Prepared snapshot for today and the authenticated driver.
