# State Machines (Draft – Pending Final Approval)

## 1. DeliveryRoute

```
Draft → Published → Assigned → Active → Completed
                 ↘ Cancelled
                 ↘ Superseded (only before lock)
```

- Transition to **Active** happens only when the driver starts the shift (sets `locked_at`).
- Once Active, no return to Assigned and no membership/order changes.

## 2. DeliveryStop (outcome)

```
Pending → Completed
       → Partial
       → Failed
       → Skipped (only with approved reason)
```

## 3. Order (delivery_status)

```
Pending → Loaded → Delivered
                → PartiallyDelivered
                → Failed
                → Refused
                → Returned
                → Cancelled
```

Exact allowed transitions and required reason codes are still **Pending Product Owner Approval** (see Decision Register D-15).

## 4. OrderLine quantities

Tracked via numeric fields rather than a complex state machine:
- ordered_qty
- loaded_qty
- delivered_qty
- returned_qty

Business rules for consistency will be finalized with the state model.
