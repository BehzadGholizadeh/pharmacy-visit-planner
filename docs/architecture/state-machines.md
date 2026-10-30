# State Machines (Draft – Pending Final Approval)

## 1. DeliveryRoute

The route is planned, finalized and assigned on the previous day.

~~~
Draft → Finalized → Assigned → Active → Completed
                         ↘ Cancelled (exception policy to be approved)
~~~

- Route content may be edited, reordered or reassigned only while the plan is Draft.
- Finalization on the previous day freezes the assigned driver, stop membership, stop sequence, order membership and linked manifest for that service date.
- After finalization, the manager cannot edit the route or publish a replacement version for that service date.
- Assigned means that the finalized snapshot has been published to the warehouse and made available to the driver app.
- Active is set when the driver starts the shift; it records operational start and does not create the immutability boundary.
- Offline event synchronization must never replace or mutate the finalized route/manifest snapshot.

## 2. Warehouse Manifest

~~~
Draft → Finalized/Published → InPreparation → Prepared
                                         ↘ Discrepancy
~~~

- The manifest is generated from and linked to the same finalized route version.
- Warehouse preparation takes place on the previous day using that exact manifest.
- Preparation status may be updated as a workflow/audit field, but manifest contents and quantities remain frozen after finalization.
- A discrepancy must be surfaced as an exception; it must not silently update the finalized manifest.
- Exact discrepancy resolution, dispatch release and whether preparation is a hard precondition for shift start remain pending Product Owner approval.

## 3. Driver Shift

~~~
NotStarted → StartedOnline
           ↘ StartedOffline
StartedOnline / StartedOffline → Ended
~~~

- Shift start is allowed online or offline only when the exact finalized route and matching manifest snapshot are locally complete and assigned to the current driver and service date.
- If the snapshot is missing, incomplete, corrupt or mismatched, shift start is blocked with a clear actionable message.
- SHIFT_STARTED is persisted locally first and synchronized later if offline.
- Route/manifest finalization happened the previous day and is independent from shift-start state.

## 4. DeliveryStop (outcome)

~~~
Pending → InProgress → Completed
                    → Partial
                    → Failed
                    → Skipped (only with approved reason)
~~~

Stop outcome should be derived from the orders/lines at that stop where practical; exact aggregation rules require approval.

## 5. Order (delivery_status)

~~~
Ready → Loaded → Delivered
               → PartiallyDelivered
               → Failed
               → Refused
               → Returned (return-to-warehouse process must be defined)
~~~

Cancellation timing and legal transitions remain pending Product Owner approval. A post-finalization order exception must not change the current day's route or manifest.

## 6. OrderLine quantities

Track separately:
- ordered_qty
- expected_qty_in_manifest
- loaded_qty (if actual load confirmation is approved)
- delivered_qty
- returned_qty (only after the meaning and return workflow are defined)

Do not conflate unshipped, undelivered, refused and physically returned quantities. Quantity validation rules remain pending final approval.
