# Phase 1 – Driver MVP (Controlled Mock Data)

**Prerequisite:** Phase 0 exit criteria met.

## Goal

A fully usable Driver experience on device using realistic **mock** data:

- Pre-shift route review
- Start Shift → route becomes locked
- Ordered stop list + next-stop focus
- Stop detail with multiple orders and order lines
- Record Delivered / Partially Delivered / Failed / Returned (with quantities where applicable)
- Local persistence (Room) + event outbox
- External navigation handoff
- Tests that prove the route cannot change after lock

## Gemini Prompt Guidance

Always instruct Gemini:

> Work only on the Driver delivery flow.  
> Do not implement Visitor features.  
> Do not allow any code path that mutates stop order or membership after shift start.  
> Use the domain model and JSON examples in docs/architecture/.  
> Prefer the smallest possible changes. Do not rewrite existing files unnecessarily.

## Definition of Done

- App builds and runs on emulator/device.
- Tester can complete a full simulated day (including partial and failed deliveries).
- Killing the app and restarting restores the locked route and pending events.
- Unit/UI tests cover the lock invariant.
