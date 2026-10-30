# Product Review Addendum – Previous-Day Route Freeze, Warehouse Preparation and Offline Start

**Date:** 2026-10-30  
**Author:** ChatGPT review of Product Owner clarification  
**Related:** Driver Delivery PRD v1.1, Decision Register, Delivery Domain Model, Data Contract and Phase 0/1.

## 1. Product Owner clarification (confirmed)

The route is determined on the previous day. The manager is not allowed to change it afterward. This is also a warehouse requirement: the warehouse prepares the goods on the previous day using that same route/manifest.

This means the previous-day finalization is the immutability boundary. It is not the moment when the driver presses Start Shift.

## 2. Required operational sequence

### Previous day

1. Prepare and review the route for the next service date.
2. Confirm the driver assignment, ordered stops, orders and order-line quantities.
3. Finalize the route and its linked manifest as one versioned snapshot.
4. Publish the same snapshot to the warehouse and driver app.
5. Warehouse prepares/stages goods from that manifest.
6. Driver app downloads and verifies the complete route and matching manifest, then persists them locally.
7. The app shows “Ready for next shift / Available offline” only when the snapshot is complete and consistent.

### Service date

1. Driver opens the app online or offline.
2. The app validates the cached route, manifest, assigned driver and service date.
3. Driver starts the shift. Shift start is recorded locally; it does not establish the route freeze.
4. Driver executes the fixed stop order and records delivery events.
5. Events are persisted locally and synchronized later when connectivity returns.

## 3. Exact offline-start rule

**Offline shift start is allowed only when the exact finalized route and its matching manifest were successfully downloaded and stored locally on the previous day.**

Local validation must confirm:
- Route status is Finalized/Assigned.
- Service date matches the current date in Asia/Tehran.
- Assigned driver matches the authenticated local session.
- Route ID/version and manifest ID/version match.
- Required route/stop/order/line/manifest data is complete and integrity checks pass.

If any condition fails, the app blocks shift start and displays a clear actionable message. It must not guess, use another driver's data, silently fall back to a different version, or pretend the route is current.

Once the shift starts, synchronization may upload queued events but cannot replace the route or manifest snapshot.

## 4. Warehouse consistency rule

The warehouse and driver must work from the same route-linked manifest snapshot. The manifest should reference:
- route_id
- route_version
- manifest_id
- manifest_version
- service_date
- assigned_driver_id

The warehouse prepares goods on the previous day from this manifest. Preparation discrepancies must be recorded and escalated; they must not silently rewrite the finalized route or manifest.

The exact picking, checking, staging, dispatch and discrepancy workflow remains open under D-12. This addendum does not assume barcode scanning, physical truck loading on the previous day, or a particular warehouse system.

## 5. Technical modeling correction

Keep these timestamps distinct:
- finalized_at: previous-day time when route/manifest are frozen.
- downloaded_at: time the driver device persisted the snapshot.
- prepared_at: time warehouse preparation was recorded.
- shift_started_at: actual start of the driver's service-day shift.

Do not use locked_at to mean “locked when the driver starts” if the route is already immutable from the previous day.

Every shift-start and delivery event must reference both the route ID/version and manifest ID/version.

## 6. Items intentionally left open

- Exact previous-day planning/finalization cutoff time.
- The detailed warehouse picking/checking/staging/dispatch process.
- How preparation shortages or discrepancies are handled before dispatch.
- Exact offline fallback if the app has no valid local snapshot.
- Production order source, API ownership and synchronization contract.

The confirmed rule is that the route is finalized the previous day, the manager cannot change it after finalization, and the warehouse prepares from the same manifest. The technical offline-start policy above is the recommended implementation of that rule and should be explicitly confirmed in the Decision Register.

## 7. Required Grok follow-up

Update the active PRD, domain model, route/manifest JSON, state machines, Phase 0 and Phase 1 prompt to reflect this addendum. Keep all documents consistent. Do not start implementation and do not modify the existing Python Visitor planner.
