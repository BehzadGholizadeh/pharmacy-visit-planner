# Data Contract – Example JSON (Draft)

These examples are **proposals** for review. Field names and exact enums are subject to Product Owner approval.

## 1. Assigned Route (downloaded before shift)

```json
{
  "route_id": "DR-20261030-0042",
  "version": 3,
  "service_date": "2026-10-30",
  "timezone": "Asia/Tehran",
  "assigned_driver_id": "DRV-1008",
  "status": "Assigned",
  "published_at": "2026-10-29T18:40:00+03:30",
  "locked_at": null,
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
          "delivery_status": "Pending",
          "lines": [
            {
              "order_line_id": "OL-1",
              "sku": "MED-1001",
              "product_name": "آموکسی‌سیلین ۵۰۰",
              "ordered_qty": 10,
              "loaded_qty": 10,
              "delivered_qty": 0,
              "returned_qty": 0
            }
          ]
        }
      ]
    }
  ]
}
```

## 2. Shift Start (lock) Event

```json
{
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event_type": "SHIFT_STARTED",
  "route_id": "DR-20261030-0042",
  "version": 3,
  "actor_id": "DRV-1008",
  "device_timestamp": "2026-10-30T08:02:15+03:30"
}
```

## 3. Partial Delivery Event

```json
{
  "event_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "event_type": "ORDER_PARTIALLY_DELIVERED",
  "route_id": "DR-20261030-0042",
  "version": 3,
  "stop_id": "ST-001",
  "order_id": "ORD-77821",
  "lines": [
    {
      "order_line_id": "OL-1",
      "delivered_qty": 7,
      "returned_qty": 0
    }
  ],
  "reason_code": "CUSTOMER_PARTIAL_ACCEPT",
  "note": "سه عدد باقی‌مانده فردا تحویل شود",
  "actor_id": "DRV-1008",
  "device_timestamp": "2026-10-30T09:18:42+03:30"
}
```

## Notes

- Client generates `event_id` (UUID) so retries are idempotent.
- Server must reject any event whose route version does not match the locked version for that driver/shift (or define explicit reconciliation).
