# Pharmacy Visit Driver — Android

Standalone native Android application for drivers delivering confirmed pharmacy orders.

The Driver delivery plan is independent from the existing Python Visitor planner. Do not reuse or modify the Visitor route-generation algorithm as part of this application.

## Development environment

The current implementation workflow uses **Google AI Studio — Build — Android** for native Kotlin/Jetpack Compose development. Android Studio may also be used for local inspection, Gradle sync, debugging, and device testing.

1. Open the Android project from the project files in Google AI Studio's Android Build environment.
2. Follow the active instructions in `docs/phases/gemini-phase-01-prompt.md` one implementation slice at a time.
3. Keep changes small, compiling, and reviewable. Do not rewrite unrelated files.

## Stack

- Kotlin 2.0.21
- Jetpack Compose + Material 3
- Manual constructor injection via `AppContainer` and `ViewModelProvider.Factory`
- Room for durable local storage
- KSP for Room code generation
- Navigation Compose
- Java Time with the fixed business timezone `Asia/Tehran`

Hilt is intentionally not used.

## Database isolation

- Operational data: `driver_operational.db`
- Debug/QA fixtures: `driver_debug_scenarios.db` (debug builds only)

Never reset or seed the debug scenario database into the operational database. A debug reset must never erase an operational active shift.

## Current status

- Slice 1 foundation: Manual DI, Kotlin domain models, Tehran clock, Room/KSP dependencies.
- Slice 2 onward: Room snapshot/progress persistence, warehouse preparation state, repository/use cases, screens, and acceptance tests.
- Production ERP/API integration and Visitor features are out of Phase 1 scope.
