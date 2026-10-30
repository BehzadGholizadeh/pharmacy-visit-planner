# Driver Module Readiness Review
## Product and Architecture Gaps Before Gemini Implementation

**Review date:** 2026-10-30  
**Reviewed branch:** `main`  
**Scope:** Documentation and Android scaffold only. This review does not authorize implementation or changes to the existing Python planner.

## 1. Executive assessment

The separate `android/` module and the initial product documentation are a useful start. The current Android code is only a UI scaffold, not an operational driver application. The product and integration design are not yet complete enough for Gemini to implement the full feature set safely.

**Recommendation:** complete and approve the product/data/architecture decisions in this document first. Then implement incrementally, starting with a stable Phase 0 contract and a narrow Phase 1 MVP.

Do not rewrite the Python planning algorithm. Do not move or reorganize the existing Python project. Keep the Android application isolated under `android/`.

## 2. Confirmed repository observations

The following are observations from the files reviewed on `main`, not assumptions about future work:

1. `README.md` describes the existing Python pipeline and points to the Android module and phased documents.
2. `plan_routes.py` writes Excel visit plans, including fields such as `visitor` (for example `V0001`), `day`, `week`, `weekday`, `group`, `stop`, `arrive`, `leave`, `travel_min`, `travel_km`, `gln`, `name`, `address`, `lat` and `lon`.
3. The planner's `day` and `week` are relative to the configured visit cycle. The inspected output logic does not assign a concrete Gregorian calendar date to every visit.
4. The planner currently produces Excel output files; no driver-facing REST API, route-publishing workflow or mobile data contract was found in the reviewed files.
5. `clean.py` maps source fields including GLN, pharmacy name, owner/contact, address and postal code. A pharmacy phone field is not present in the reviewed source-column mapping.
6. `driver-module-prd.md` describes the app as a driver/visitor app and requires an offline-first daily route experience.
7. `phase-01-mvp.md` proposes Kotlin, Jetpack Compose, Material 3, Navigation Compose, Room, Retrofit/OkHttp, DataStore, WorkManager and Hilt.
8. The current Android scaffold includes `DriverApp.kt`, `MainActivity.kt`, a mock login screen, a fake Today's Route screen and a navigation host.
9. The mock login advances without validating an OTP. The Today's Route screen uses hard-coded sample stops and hard-coded summary text.
10. The navigation host declares a stop-detail route string and navigates to it when a stop is clicked, but no stop-detail destination is registered yet.
11. No Room entity/DAO/database implementation or domain/repository implementation was found in the reviewed Android paths.
12. `phase-02-offline-sync-photo.md` is a short feature list, not a detailed implementation/acceptance specification. `phase-03-advanced.md` is also a short feature list.
13. The README's current-status text and `android/README.md` use different descriptions of Phase 1 readiness. These status statements should be reconciled.
14. The current Gradle files declare Kotlin 2.0.21 and Compose Compiler Extension 1.5.15, but do not declare/apply the Kotlin Compose compiler Gradle plugin. Verify and correct the build configuration against the official compatibility guidance before feature implementation.
15. A Gradle wrapper and automated Android test coverage were not found in the reviewed paths. Confirm repository contents and add the standard wrapper/test setup if missing.

## 3. Product decisions that must be resolved

### 3.1 Driver versus visitor identity

The Python planner assigns work to a `visitor` (e.g. `V0001`), while the new app is described as a driver app.

Decide explicitly:
- Is one person both the driver and the pharmacy visitor?
- Is a driver a separate person who transports one or more field visitors?
- Can one employee have multiple roles?
- Is one planner visitor ID permanently mapped to one application account, or can assignments change over time?

Do not silently equate driver ID, employee ID, user ID and planner visitor ID. Define separate identifiers and their mapping.

### 3.2 Route cycle and calendar dates

Define how a planner cycle becomes dated daily assignments:
- Cycle start date and time zone (Iran business operations should explicitly use `Asia/Tehran`).
- Mapping of planner `day` / `week` / `weekday` to a real date.
- Working-day calendar, holidays and exceptional non-working days.
- What happens when a route is generated late, a day is missed, or a driver is reassigned.
- Whether yesterday's incomplete stops carry over, remain overdue, or require manager action.

Persist actual route date and assignment identity. Do not derive today's route from a device clock plus a relative cycle number alone.

### 3.3 Route publishing and lifecycle

Define the manager/planner workflow:
1. Generate a plan.
2. Review and validate it.
3. Publish a version.
4. Assign it to a driver account.
5. Make it available for download.
6. Notify affected drivers when a newer version is published.
7. Reconcile a route that has already started.

Specify route states such as Draft, Published, Assigned, Active, Completed, Cancelled and Superseded, including allowed transitions and who can perform them.

A route update must not silently reorder stops after the driver has started. Define whether the driver must acknowledge a material change and how already-recorded visits are preserved.

### 3.4 Driver experience and operating rules

Specify at least these screens and states:
- Login/session restoration.
- Today overview: date, driver identity, route status, completed/remaining counts and last sync time.
- Next-stop-focused view with a prominent navigation action.
- Ordered stop list with clear status and sequence.
- Stop details: pharmacy name, address, available contact data, coordinates, planned arrival and planned service duration.
- Navigation-app selection/launch and fallback when an app is not installed.
- Complete, failed and skipped visit flows.
- Reason selection for failed/skipped visits, with optional notes.
- Route completion and end-of-day summary.
- Contact manager/help and emergency/error states.
- Empty route, no connection, stale route, expired session and sync-conflict states.

Prioritize one-handed use, large touch targets, readable contrast and minimal typing. Use Persian-first UI, RTL, Persian typography, Persian digits where appropriate and Jalali date presentation in the MVP; these are usability requirements, not late-stage decoration.

Clearly distinguish planned/estimated arrival time from a confirmed appointment window. The current planner calculates estimates; it does not establish appointments with pharmacies.

### 3.5 Source data and contact details

The reviewed `clean.py` source-column mapping does not include a pharmacy phone number. Decide whether phone details will be supplied by a separate trusted source, added to an import, or omitted when unavailable.

Define validation and fallback behavior for missing/invalid address, GLN, coordinates, phone, arrival estimate and service duration. Do not fabricate contact information or coordinates.

## 4. Required system architecture and integration contract

Before implementing real networking, define a versioned, documented contract between the Python planner/manager workflow, backend and Android app.

At minimum, specify:
- Driver account and employee identity.
- Planner visitor-to-driver assignment mapping and effective dates.
- Route ID, route version, publication status, assignment and actual route date.
- Stop ID, stable stop sequence, GLN, pharmacy name, address, optional phone, coordinates, planned arrival, travel estimate and planned service duration.
- Visit event ID, stop ID, route version, actor, event type, status, reason, note, device timestamp and server-received timestamp.
- Optional evidence metadata (photo/signature) and upload state.
- Sync cursor/watermark and server version.
- API authentication, authorization, error model, pagination and compatibility/version policy.

Include realistic JSON request/response examples and field-level rules (required/optional, type, format, timezone, null handling and identifier stability).

Do not make the Android app read or parse the planner's Excel workbook as its permanent production integration. Excel can remain a planning/export artifact; introduce a controlled import/publishing boundary or backend API. Define the owner of that boundary.

## 5. Offline-first behavior and data consistency

"Offline-first" must be specified as behavior, not just a technology choice.

Define:
- A downloaded route can be viewed and used without a network connection.
- Visit actions are saved locally before the UI reports success.
- Pending events survive app restart, process death and device reboot.
- Each event has a stable unique ID and is safe to retry (idempotency).
- Retries use bounded backoff and expose a clear sync state.
- A successful upload is acknowledged by the server before the event is removed from the pending queue.
- Conflicts caused by a newer route version, reassignment, duplicate action or manager correction have explicit rules.
- Logout/account switching does not expose another driver's cached route or pending data.
- Stale route data is visibly marked, with a policy for whether new visits can still be recorded.

Define and test the behavior for: no network all day, network loss during upload, app force-stop, device reboot, duplicate retry, route re-publication during a shift, and two devices signed in to the same account.

Do not promise offline navigation unless the selected navigation provider and maps support the required offline behavior. Opening an installed navigation app is different from offline routing.

## 6. Visit status, evidence and location privacy

Define a state machine for visits. At minimum, clarify:
- Whether status can move from Pending to Completed, Failed or Skipped.
- Whether a completed visit can be edited, reversed or corrected, and by whom.
- Whether Failed/Skipped requires a reason.
- Whether a note is optional and length-limited.
- Whether evidence is required for any status or only selected cases.
- How photo/signature data is compressed, stored, retried, retained and deleted.
- Whether visit events need a server audit trail.

The PRD calls live manager tracking a non-goal, while Phase 3 mentions optional live location sharing. Resolve this contradiction. Do not request background location permission or collect continuous location by default. If location is later approved, specify purpose, consent, minimum frequency, retention, visibility and stop-sharing controls.

## 7. Android implementation readiness

Before Phase 1 feature work:
- Verify a clean Gradle sync and debug build on the target Android Studio/JDK environment.
- Resolve Kotlin/Compose compiler plugin compatibility. The current Kotlin 2.0.21 plus Compose compiler extension 1.5.15 setup needs correction/verification.
- Confirm Gradle wrapper files and pin the wrapper version.
- Keep dependencies versioned and avoid unnecessary libraries before the relevant phase.
- Register all navigation destinations before exposing navigation actions.
- Define Room schema, migrations and repository interfaces before connecting UI to data.
- Add unit tests for domain rules and DAO/repository tests; add UI/navigation tests for critical flows.
- Add build/test instructions and a documented minimum supported Android version.
- Verify RTL, accessibility, font scaling, dark/light behavior and small-screen layouts.

Use stable IDs for list keys and domain entities. Do not keep route/status data in hard-coded Compose sample lists once the repository layer is introduced.

## 8. Recommended revised delivery phases

### Phase 0 — Product, contract and build foundation
**Goal:** remove unresolved architecture decisions before building operational behavior.

Deliverables:
- Approved driver/visitor role model and account mapping.
- Dated route-cycle and calendar rules.
- Route publication/assignment lifecycle.
- Versioned API/data contract with JSON examples.
- Offline event/sync/conflict specification.
- Visit status state machine and evidence policy.
- Corrected Android build configuration, wrapper and test baseline.
- Updated PRD, screen specifications and phase-specific Gemini prompts.

**Exit criteria:** no critical unresolved decision about identity, dated assignment, route delivery or offline visit-event ownership.

### Phase 1 — Functional Android MVP with controlled mock data
**Goal:** validate the driver workflow end-to-end on a device before production backend integration.

Deliverables:
- Persian-first login/session mock clearly labelled as non-production.
- Local route data using repository abstractions and Room.
- Today overview, ordered stops, next stop and stop detail.
- External navigation handoff with provider/fallback behavior.
- Complete/Failed/Skipped actions with defined reasons.
- Local persistence across app restart.
- Route progress and visible local/sync state.
- Unit/UI tests for core flow.

**Exit criteria:** a tester can complete a complete simulated working day, including failed/skipped stops and app restart, without hard-coded UI state or crashes.

### Phase 2 — Backend, reliable sync and field evidence
**Goal:** connect the approved publishing/API contract and operate reliably with intermittent connectivity.

Deliverables:
- Authenticated API and driver assignment.
- Route download, version checks and controlled refresh.
- Persistent local outbox and idempotent event synchronization.
- Conflict handling, retry/backoff and diagnostics.
- Photo evidence only if its operational purpose and retention policy are approved.
- Manager contact and useful sync diagnostics.
- Integration tests for outage/retry/reassignment scenarios.

**Exit criteria:** no visit event is lost or duplicated under the agreed retry/conflict test matrix.

### Phase 3 — Operational enhancements
**Goal:** add only features that improve measurable field outcomes.

Candidates:
- Traffic-aware ETA, clearly labelled as an estimate.
- Push alerts for meaningful route changes.
- End-of-day reporting and performance metrics.
- Next-stop widget and multi-day view.
- Optional location sharing only after privacy/consent approval.
- Additional accessibility/theme/language enhancements.

**Exit criteria:** each feature has an owner, privacy/permission impact, measurable acceptance criteria and regression coverage.

## 9. Minimum acceptance and test matrix

| Scenario | Expected behavior |
|---|---|
| First launch, valid test login | Driver reaches the assigned route only |
| Driver has no assigned route | Clear empty state; no sample route presented as real |
| Route has 10 stops | Stable ordering and correct remaining/completed count |
| Open stop details | Correct stop data and clear return navigation |
| Navigation app installed/unavailable | Correct handoff or actionable fallback |
| Complete a stop offline | Saved locally immediately and reflected in progress |
| Fail/skip without required reason | Action blocked with clear explanation |
| App is killed after an offline event | Event and local status are restored |
| Network returns | Event syncs once; retry does not duplicate it |
| Route is republished mid-shift | Defined change/acknowledgement flow; existing events preserved |
| Driver account changes on device | Previous driver's private route/events are not exposed |
| Missing phone/coordinates | Graceful omission/fallback; no invented data |
| Persian/Jalali/RTL and large fonts | Correct readable layout without clipping |
| No map app installed | Driver receives a useful fallback/error |
| End-of-day | Accurate summary based on persisted visit events |

## 10. Instructions for Grok review

Review this document against the current repository, correct any mistaken observation, and produce a revised, internally consistent PRD and phase plan.

For every item, classify it as:
- **Confirmed fact** (supported by current code/data),
- **Decision required** (requires product-owner input),
- **Recommended design** (proposal, not an existing capability),
- **Implementation task** (must be added in a named phase).

Do not invent decisions on behalf of the product owner. Present a short decision register for unresolved items. Keep the existing Python planner behavior and files intact unless a separately approved requirement explicitly calls for a change.

Do not start Android implementation, do not modify Python logic, and do not create or alter production API/backend code during this review. First return the revised PRD, architecture, contracts, UX specifications, phased prompts and decision register for approval.

## 11. Source files reviewed

- `README.md`
- `clean.py`
- `plan_routes.py`
- `timing.py`
- `docs/product/driver-module-prd.md`
- `docs/phases/phase-01-mvp.md`
- `docs/phases/phase-02-offline-sync-photo.md`
- `docs/phases/phase-03-advanced.md`
- `android/README.md`
- `android/build.gradle.kts`
- `android/settings.gradle.kts`
- `android/app/build.gradle.kts`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/src/main/java/com/pharmacyvisit/driver/DriverApp.kt`
- `android/app/src/main/java/com/pharmacyvisit/driver/MainActivity.kt`
- `android/app/src/main/java/com/pharmacyvisit/driver/presentation/login/LoginScreen.kt`
- `android/app/src/main/java/com/pharmacyvisit/driver/presentation/today/TodayRouteScreen.kt`
- `android/app/src/main/java/com/pharmacyvisit/driver/presentation/navigation/DriverNavHost.kt`
