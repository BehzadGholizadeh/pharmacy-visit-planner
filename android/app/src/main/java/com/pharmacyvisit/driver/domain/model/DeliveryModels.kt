package com.pharmacyvisit.driver.domain.model

import java.time.Instant
import java.time.LocalDate
import java.util.UUID

/**
 * Immutable route data captured at previous-day finalization and downloaded to the device.
 * Null timestamps/checksum are representable so invalid fixtures can be tested and blocked.
 */
data class RouteSnapshot(
    val routeId: String,
    val routeVersion: Int,
    val serviceDate: LocalDate,
    val timezoneId: String = "Asia/Tehran",
    val assignedDriverId: String,
    val snapshotStatus: RouteSnapshotStatus,
    val publishedAt: Instant?,
    val finalizedAt: Instant?,
    val finalizedBy: String?,
    val downloadedAt: Instant?,
    val snapshotChecksum: String?,
    val snapshotComplete: Boolean
)

/** Immutable identity and route linkage of the manifest; preparation progress is stored separately. */
data class ManifestSnapshot(
    val manifestId: String,
    val manifestVersion: Int,
    val routeId: String,
    val routeVersion: Int,
    val serviceDate: LocalDate,
    val assignedDriverId: String,
    val publishedToWarehouseAt: Instant?
)

/** Mutable until the associated route becomes ACTIVE; then it is read-only for that service run. */
data class WarehousePreparationState(
    val manifestId: String,
    val preparationStatus: WarehousePreparationStatus,
    val preparedAt: Instant?,
    val preparedBy: String?
)

/** Actual quantity confirmed by warehouse, separate from immutable expectedManifestQty. */
data class WarehouseLinePreparationState(
    val orderLineId: String,
    val preparedQty: Int,
    val updatedAt: Instant?
)

/** Immutable pharmacy/stop content and order membership from the finalized route. */
data class StopSnapshot(
    val stopId: String,
    val routeId: String,
    val sequence: Int,
    val pharmacyName: String,
    val address: String,
    val latitude: Double?,
    val longitude: Double?,
    val phone: String?
)

/** Immutable order membership. Initial readiness is captured from the finalized snapshot. */
data class OrderSnapshot(
    val orderId: String,
    val stopId: String,
    val routeId: String,
    val initialReadinessStatus: OrderDeliveryStatus = OrderDeliveryStatus.READY_FOR_DELIVERY
)

/** Immutable line facts; actual prepared quantity is stored in WarehouseLinePreparationState. */
data class OrderLineSnapshot(
    val orderLineId: String,
    val orderId: String,
    val sku: String,
    val productName: String,
    val orderedQty: Int,
    val expectedManifestQty: Int
)

data class DeliverySnapshot(
    val route: RouteSnapshot,
    val manifest: ManifestSnapshot,
    val stops: List<StopSnapshot>,
    val orders: List<OrderSnapshot>,
    val orderLines: List<OrderLineSnapshot>,
    val warehousePreparation: WarehousePreparationState,
    val warehouseLinePreparation: List<WarehouseLinePreparationState>
)

data class DriverSessionState(
    val sessionId: String,
    val authenticatedDriverId: String,
    val loggedInAt: Instant
)

data class RouteProgressState(
    val routeId: String,
    val routeVersion: Int,
    val operationalStatus: RouteOperationalStatus,
    val shiftStartedAt: Instant?,
    val shiftCompletedAt: Instant?
)

data class OrderProgressState(
    val orderId: String,
    val stopId: String,
    val routeId: String,
    val deliveryStatus: OrderDeliveryStatus,
    val reasonCode: String?,
    val note: String?,
    val recordedByEventId: UUID?,
    val updatedAt: Instant?
)

data class OrderLineProgressState(
    val orderLineId: String,
    val orderId: String,
    val deliveredQty: Int,
    val updatedByEventId: UUID?
)

/** Combined read model; each source value remains persisted in its own immutable/mutable table. */
data class OrderLineQuantityView(
    val orderedQty: Int,
    val expectedManifestQty: Int,
    val preparedQty: Int,
    val deliveredQty: Int
) {
    val remainingPreparedQty: Int
        get() = preparedQty - deliveredQty

    val unfulfilledOrderQty: Int
        get() = orderedQty - deliveredQty
}

data class DeliveryEventLine(
    val orderLineId: String,
    val deliveredQty: Int
)

/** Append-only business event; sync status may change as part of outbox processing. */
data class DeliveryEvent(
    val eventId: UUID,
    val eventType: DeliveryEventType,
    val routeId: String,
    val routeVersion: Int,
    val manifestId: String,
    val manifestVersion: Int,
    val actorId: String,
    val deviceTimestamp: Instant,
    val stopId: String? = null,
    val orderId: String? = null,
    val lines: List<DeliveryEventLine> = emptyList(),
    val reasonCode: String? = null,
    val note: String? = null,
    val syncStatus: SyncStatus = SyncStatus.PENDING
)
