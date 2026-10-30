# Driver Delivery Module – PRD v1.1 (Final for Phase 0)

**Status:** Aligned with Product Owner decisions of 2026-10-30  
**Timezone:** Asia/Tehran  
**Package:** `com.pharmacyvisit.driver`

---

## 1. Goal

A standalone Android app that lets a driver:

1. Receive the finalized route + matching manifest the previous day.
2. Start the shift offline (when the snapshot is valid and Prepared).
3. Follow the fixed ordered stops.
4. Record delivery outcomes (including partial quantities and reasons).
5. Persist events locally and sync later.

## 2. Confirmed Rules (non-negotiable)

- Previous-day finalization: route + manifest become immutable after finalization.
- Manager cannot change a finalized route for that service date.
- Warehouse prepares from the same manifest on the previous day.
- Offline start allowed only with complete, matching, Prepared local snapshot for today + authenticated driver.
- No mid-day route mutation of any kind.
- No Visitor features in this app.
- No live location, no production proof-of-delivery, no real ERP in Phase 1.

## 3. Phase 1 Scope (Mock)

- Deterministic Mock Repository (multi-stop, multi-order, multi-line).
- Pre-shift view of route + Prepared status.
- Shift start (online or offline) with lock of the already-finalized snapshot.
- Ordered stop list + next-stop focus.
- Stop detail with orders and lines.
- Actions: Delivered / PartiallyDelivered / Failed / Refused (reason required for last three).
- Local Room persistence + event outbox.
- External navigation handoff (Google Maps / Neshan / Waze).
- End-of-day summary; unresolved → Pending Manager Review (no auto carry-over).
- Persian-first, RTL, large touch targets.

## 4. Explicit Non-Goals for Phase 1

- Real authentication / OTP production backend
- Real order source / ERP
- Photo, signature, OTP, GPS proof
- Barcode scanning or warehouse app
- Live location
- Visitor role
- Automatic retry / carry-over into next day
- Any mutation of a finalized route/manifest

## 5. Success Criteria (Phase 1)

- Driver can start a full simulated day offline after previous-day download.
- Route order and membership never change after finalization / shift start.
- All delivery actions survive process death and are queued for sync.
- Missing or mismatched snapshot blocks offline start with a clear message.
