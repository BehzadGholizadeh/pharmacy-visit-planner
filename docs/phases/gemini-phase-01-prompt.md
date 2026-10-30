# Gemini 3.8 / Android Studio – Phase 1 Prompt (Copy-Paste Ready)

```
You are an expert Android engineer working on an existing project.

Project root: android/
Application ID / namespace: com.pharmacyvisit.driver

IMPORTANT RULES
1. Work ONLY on the Driver delivery flow. Do NOT implement any Visitor features.
2. Do NOT rewrite the whole project. Make the smallest possible changes.
3. The route + matching manifest are finalized the PREVIOUS day and are IMMUTABLE thereafter.
4. Offline shift start is allowed ONLY when the exact previous-day finalized route AND matching manifest are fully present locally, assigned to the authenticated driver, valid for today’s date in Asia/Tehran, and marked Prepared. Otherwise BLOCK start with a clear Persian message.
5. After finalization / shift start, NO code path may add, remove, reorder stops or change orders/quantities on the route.
6. Use the domain model and state machines described in docs/architecture/.
7. Phase 1 uses a deterministic local Mock Repository only. No real network, ERP, photo, signature, OTP or GPS proof.
8. Persian-first UI, RTL, large touch targets, Material 3, Jetpack Compose, Hilt, Room, Navigation Compose.

REQUIRED WORK FOR PHASE 1

A. Domain & Data
- Models: DeliveryRoute, DeliveryManifest, DeliveryStop, Order, OrderLine, DeliveryEvent
- Room entities + DAOs + Database
- MockRepository that returns a realistic multi-stop route (at least 5 stops, some stops with multiple orders, some orders with multiple lines). Mark the manifest as Prepared.
- Event outbox (client-generated UUID, sync_status = Pending)

B. Screens (Compose)
1. Login (simple mock – any driver ID / PIN is fine; clearly labelled as mock)
2. Pre-shift / Today overview: show service date, route version, manifest Prepared status, list of stops summary
3. Start Shift button – enabled only when offline-start rules are satisfied
4. Active route – ordered LazyColumn of stops + prominent “Next stop”
5. Stop detail – pharmacy info, optional phone, list of orders and lines with quantity controls
6. Outcome actions: Delivered / Partially Delivered / Failed / Refused (last three require reason)
7. End-of-day summary

C. Behaviour
- Starting shift sets shift_started_at and moves route to Active
- All outcomes create DeliveryEvents first (local success), then update local state
- Process death must restore the same locked snapshot and pending events
- Navigation intent to Google Maps / Neshan / Waze using coordinates or address

D. Tests
- Unit test: offline start is blocked when snapshot is missing or not Prepared
- Unit test: after shift start, attempts to mutate stop order are rejected
- Basic UI test for start-shift happy path

E. Build
- Ensure the project uses the Kotlin Compose Compiler plugin (org.jetbrains.kotlin.plugin.compose) compatible with Kotlin 2.0.x
- Do not re-introduce kotlinCompilerExtensionVersion if the Compose plugin is applied

Deliver working, compiling code. Prefer extending existing files over creating parallel implementations.
```
