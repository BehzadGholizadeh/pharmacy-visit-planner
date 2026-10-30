# Phase 1 – MVP: Driver Daily Route App

**Goal**: A working Android app where a driver can log in, see today’s ordered list of pharmacies, navigate to each one, and mark the visit status. Fully offline-capable.

## Tech Stack (recommended for Gemini)
- Kotlin
- Jetpack Compose
- Material 3
- Navigation Compose
- Room (local DB)
- Retrofit + OkHttp (API)
- DataStore (preferences)
- WorkManager (background sync)
- Hilt (DI)
- Clean Architecture (data / domain / presentation)

## Project Structure to create
```
android/
├── app/
│   └── src/main/java/com/pharmacyvisit/driver/
│       ├── DriverApp.kt
│       ├── di/
│       ├── data/
│       │   ├── local/
│       │   ├── remote/
│       │   └── repository/
│       ├── domain/
│       │   ├── model/
│       │   └── usecase/
│       ├── presentation/
│       │   ├── login/
│       │   ├── today/
│       │   ├── stopdetail/
│       │   └── components/
│       └── util/
├── build.gradle.kts
└── settings.gradle.kts
```

## Exact Tasks for this Phase
1. Create empty Android project with the structure above (Compose + Hilt + Room).
2. Define domain models: `Stop`, `DailyRoute`, `VisitStatus`.
3. Room entities + DAOs for offline storage of today’s route.
4. Fake / mock data source first (so UI can be built without backend).
5. Login screen (phone + OTP or simple PIN).
6. Today’s Route screen – vertical list of ordered stops with status chips.
7. Stop Detail screen – address, call button, Navigate button, Mark as Done / Problem.
8. Deep link / Intent to open Google Maps or Neshan with the address.
9. Basic offline-first: load from Room, sync later.

## Prompt Template for Gemini (copy-paste ready)

```
You are an expert Android developer using Kotlin + Jetpack Compose + Clean Architecture.

Create the complete Phase 1 MVP of a Driver app for pharmacy visit planning.

Requirements:
- Package: com.pharmacyvisit.driver
- Use Jetpack Compose + Material 3
- Hilt for dependency injection
- Room for local storage
- Navigation Compose
- Offline-first

Domain models needed:
- Stop (id, order, pharmacyName, address, phone, lat, lon, plannedArrival, serviceMinutes, status)
- DailyRoute (date, stops: List<Stop>)
- VisitStatus: PENDING, COMPLETED, FAILED, SKIPPED

Screens:
1. LoginScreen (phone number + OTP mock)
2. TodayRouteScreen (LazyColumn of ordered stops)
3. StopDetailScreen (info + Navigate + Mark status)

Use a fake repository first with 8-10 sample Iranian pharmacy stops in Tehran/Isfahan so the UI is fully testable.

Generate all necessary files with proper package structure. Start with the project-level and app-level build.gradle.kts, then the models, then the screens.
```

## Definition of Done
- App builds and runs on emulator
- Driver can see a realistic ordered list
- Can open navigation
- Can change status of a stop
- Data survives app restart (Room)
