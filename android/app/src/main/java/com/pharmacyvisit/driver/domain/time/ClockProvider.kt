package com.pharmacyvisit.driver.domain.time

import java.time.Clock
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId

/**
 * All delivery-calendar decisions use the Tehran business timezone, irrespective of device locale.
 * Tests can inject Clock.fixed(...) for deterministic service-date and previous-day validation.
 */
interface ClockProvider {
    val zoneId: ZoneId
    fun now(): Instant
    fun today(): LocalDate
}

class SystemClockProvider(
    private val clock: Clock = Clock.systemUTC()
) : ClockProvider {

    override val zoneId: ZoneId = ZoneId.of(DELIVERY_TIME_ZONE_ID)

    override fun now(): Instant = clock.instant()

    override fun today(): LocalDate = LocalDate.now(clock.withZone(zoneId))

    companion object {
        const val DELIVERY_TIME_ZONE_ID = "Asia/Tehran"
    }
}
