# Phase 1 – Driver MVP (Mock Data)

**Prerequisite:** Phase 0 fully closed.

## Scope
See PRD v1.1 §3.

## Gemini Prompt
The complete, copy-paste-ready prompt is in:

`docs/phases/gemini-phase-01-prompt.md`

## Definition of Done
- App builds on emulator/device.
- Full simulated day (including partial/failed with reasons) works offline after previous-day snapshot is present.
- Route/manifest never mutate after finalization.
- Process death preserves locked snapshot and outbox events.
- Unit/UI tests cover offline-start guard and immutability invariant.
