# Data Contract – Example JSON (Draft)

These examples are **proposals** for review. Field names and exact enums are subject to Product Owner approval.

The route and manifest are prepared and finalized on the previous day. Both the warehouse and the driver app must receive the same immutable route/manifest snapshot.

## 1. Finalized Assigned Route + Manifest (downloaded on previous day)

~~~json
{
  "route_id": "DR-20261031-0042",
  "version": 3,
  "service_date": "2026-10-31",
  "timezone": "Asia/Tehran",
  "assigned_driver_id": "DRV-1008",
  "status": "Finalized",
  "published_at": "2026-10-30T16:30:00+03:30",
  "finalized_at": "2026-10-30T17:00:00+03:30",
  "finalized_by": "MGR-101",
  "shift_started_at": null,
  "manifest": {
    "manifest_id": "MAN-20261031-0042",
    "manifest_version": 1,
    "route_id": "DR-20261031-0042",
    "route_version": 3,
    "service_date": "2026-10-31",
    "assigned_driver_id": "DRV-1008",
    "preparation_status": "Prepared",
    "published_to_warehouse_at": "2026-10-30T17:05:00+03:30",
    "prepared_at": "2026-10-30T19:20:00+03:30",
    "prepared_by": "WH-007"
  },
  "stops": [
    {
      "stop_id": "ST-001",
      "sequence": 1,
      "pharmacy_name": "داروخانه دکتر رضایی",
      "address": "تهران، خیابان ولیعصر، پلاک ۲۳۰",
      "lat": 35.7219,
      "lon": 51.4056,
      "phone": null,
      "orders": [
        {
          "order_id": "ORD-77821",
          "delivery_status": "Ready",
          "lines": [
            {
              "order_line_id": "OL-1",
              "sku": "MED-1001",
              "product_name": "آموکسی‌سیلین ۵۰۰",
              "ordered_qty": 10,
              "expected_qty_in_manifest": 10
            }
          ]
        }
      ]
    }
  ]
}
~~~

## 2. Local Snapshot Readiness (device-side metadata; not a server route mutation)

~~~json
{
  "route_id": "DR-20261031-0042",
  "route_version": 3,
  "manifest_id": "MAN-20261031-0042",
  "manifest_version": 1,
  "assigned_driver_id": "DRV-1008",
  "service_date": "2026-10-31",
  "downloaded_at": "2026-10-30T17:10:00+03:30",
  "snapshot_complete": true,
  "snapshot_checksum_verified": true,
  "offline_start_ready": true
}
~~~

## 3. Shift Start Event (can be persisted offline)

~~~json
{
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event_type": "SHIFT_STARTED",
  "route_id": "DR-20261031-0042",
  "route_version": 3,
  "manifest_id": "MAN-20261031-0042",
  "manifest_version": 1,
  "actor_id": "DRV-1008",
  "device_timestamp": "2026-10-31T08:02:15+03:30",
  "sync_status": "Pending"
}
~~~

## 4. Partial Delivery Event

~~~json
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
  "reason_code": "CUSTOMER_PARTIAL_ACCEPT",
  "note": "سه عدد تحویل نشد",
  "actor_id": "DRV-1008",
  "device_timestamp": "2026-10-31T09:18:42+03:30",
  "sync_status": "Pending"
}
~~~

## Contract and validation notes

- The route and its manifest must carry matching route_id, route_version, service_date and assigned_driver_id.
- The warehouse and driver app must consume the same finalized manifest version.
- Client-generated event_id (UUID) makes retries idempotent.
- Device-side readiness metadata is local state; it does not authorize changing the server's finalized route.
- The exact API endpoints, authentication, acknowledgements, error handling and retry contract remain to be specified before production integration.
- The exact preparation status flow and discrepancy resolution process remain pending Product Owner approval.
