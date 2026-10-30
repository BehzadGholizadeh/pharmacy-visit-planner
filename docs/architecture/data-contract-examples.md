# Data Contract — Immutable Snapshot, Warehouse Preparation and Delivery Progress

These examples define the Phase 1 local contract. Server/API transport details remain outside the Phase 1 mock implementation.

## 1. Finalized route snapshot (immutable)

```json
{
  "route_id": "DR-20261031-0042",
  "route_version": 3,
  "service_date": "2026-10-31",
  "timezone": "Asia/Tehran",
  "assigned_driver_id": "DRV-1008",
  "snapshot_status": "FINALIZED",
  "published_at": "2026-10-30T16:30:00+03:30",
  "finalized_at": "2026-10-30T17:00:00+03:30",
  "finalized_by": "MGR-101",
  "downloaded_at": "2026-10-30T17:10:00+03:30",
  "snapshot_checksum": "sha256:mock-checksum-value",
  "snapshot_complete": true,
  "stops": [
    {
      "stop_id": "ST-001",
      "sequence": 1,
      "pharmacy_name": "داروخانه دکتر رضایی",
      "address": "تهران، خیابان ولیعصر، پلاک ۲۳۰",
      "latitude": 35.7219,
      "longitude": 51.4056,
      "phone": null,
      "orders": [
        {
          "order_id": "ORD-77821",
          "initial_readiness_status": "READY_FOR_DELIVERY",
          "lines": [
            {
              "order_line_id": "OL-1",
              "sku": "MED-1001",
              "product_name": "آموکسی‌سیلین ۵۰۰",
              "ordered_qty": 10,
              "expected_manifest_qty": 10
            }
          ]
        }
      ]
    }
  ]
}
```

## 2. Immutable manifest snapshot

```json
{
  "manifest_id": "MAN-20261031-0042",
  "manifest_version": 1,
  "route_id": "DR-20261031-0042",
  "route_version": 3,
  "service_date": "2026-10-31",
  "assigned_driver_id": "DRV-1008",
  "published_to_warehouse_at": "2026-10-30T17:05:00+03:30"
}
```

The manifest snapshot contains identity/linkage only. It does not contain mutable preparation status or actual prepared quantities.

## 3. Warehouse preparation state (mutable before shift start, then locked)

```json
{
  "manifest_id": "MAN-20261031-0042",
  "preparation_status": "PREPARED",
  "prepared_at": "2026-10-30T19:20:00+03:30",
  "prepared_by": "WH-007",
  "lines": [
    {
      "order_line_id": "OL-1",
      "prepared_qty": 10,
      "updated_at": "2026-10-30T19:20:00+03:30"
    }
  ]
}
```

`expected_manifest_qty` is from the immutable order-line snapshot. `prepared_qty` is the actual quantity recorded by the warehouse in the separate preparation table. The driver cannot start unless preparation status is `PREPARED` and the prepared line data is complete/valid.

Once the associated route becomes `ACTIVE`, neither this state nor its line quantities may be changed for that service run.

## 4. Local snapshot readiness metadata

```json
{
  "route_id": "DR-20261031-0042",
  "route_version": 3,
  "manifest_id": "MAN-20261031-0042",
  "manifest_version": 1,
  "assigned_driver_id": "DRV-1008",
  "service_date": "2026-10-31",
  "downloaded_at": "2026-10-30T17:10:00+03:30",
  "snapshot_complete": true,
  "snapshot_checksum_verified": true
}
```

## 5. Shift start event

```json
{
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event_type": "SHIFT_STARTED",
  "route_id": "DR-20261031-0042",
  "route_version": 3,
  "manifest_id": "MAN-20261031-0042",
  "manifest_version": 1,
  "actor_id": "DRV-1008",
  "device_timestamp": "2026-10-31T08:02:15+03:30",
  "sync_status": "PENDING"
}
```

## 6. Partial delivery event

```json
{
  "event_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "event_type": "ORDER_PARTIALLY_DELIVERED",
  "route_id": "DR-20261031-0042",
  "route_version": 3,
  "manifest_id": "MAN-20261031-0042",
  "manifest_version": 1,
  "stop_id": "ST-001",
  "order_id": "ORD-77821",
  "lines": [
    {
      "order_line_id": "OL-1",
      "delivered_qty": 7
    }
  ],
  "reason_code": "PARTIAL_ACCEPTANCE_BY_PHARMACY",
  "note": "سه عدد تحویل نشد",
  "actor_id": "DRV-1008",
  "device_timestamp": "2026-10-31T09:18:42+03:30",
  "sync_status": "PENDING"
}
```

## 7. Contract invariants

- Route and manifest IDs/versions, service date and assigned driver must match exactly.
- The route's finalized timestamp and local downloaded timestamp are instants; compare their Tehran-local dates for offline-start validation.
- For a new shift: service date is today in `Asia/Tehran`; finalized local date is earlier than service date; downloaded local date is earlier than service date; and `downloaded_at >= finalized_at`.
- The warehouse and driver use the same manifest ID/version.
- `expected_manifest_qty`, actual `prepared_qty`, and delivered `delivered_qty` are separate values.
- Client-generated event UUIDs make outbox retries idempotent. Event insertion and progress updates occur in one Room transaction.
- Exact API endpoints, authentication, acknowledgements and retry policy remain deferred until production integration.
