package com.pharmacyvisit.driver.di

import android.content.Context
import com.pharmacyvisit.driver.BuildConfig
import com.pharmacyvisit.driver.domain.time.ClockProvider
import com.pharmacyvisit.driver.domain.time.SystemClockProvider

/**
 * Selects a physical database file. Room instances are wired into this container in Slice 2.
 * Debug fixtures must never share the operational database.
 */
enum class DatabaseProfile {
    OPERATIONAL,
    DEBUG_SCENARIOS
}

interface AppContainer {
    val applicationContext: Context
    val clockProvider: ClockProvider

    fun databaseName(profile: DatabaseProfile = DatabaseProfile.OPERATIONAL): String
}

class DefaultAppContainer(context: Context) : AppContainer {
    override val applicationContext: Context = context.applicationContext
    override val clockProvider: ClockProvider = SystemClockProvider()

    override fun databaseName(profile: DatabaseProfile): String =
        when (profile) {
            DatabaseProfile.OPERATIONAL -> OPERATIONAL_DATABASE_NAME
            DatabaseProfile.DEBUG_SCENARIOS -> {
                check(BuildConfig.DEBUG) {
                    "The debug scenario database is available only in debug builds."
                }
                DEBUG_SCENARIOS_DATABASE_NAME
            }
        }

    private companion object {
        const val OPERATIONAL_DATABASE_NAME = "driver_operational.db"
        const val DEBUG_SCENARIOS_DATABASE_NAME = "driver_debug_scenarios.db"
    }
}
