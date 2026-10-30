package com.pharmacyvisit.driver.domain.model

enum class RouteSnapshotStatus {
    DRAFT,
    FINALIZED,
    ASSIGNED
}

enum class RouteOperationalStatus {
    READY_TO_START,
    ACTIVE,
    COMPLETED
}

enum class WarehousePreparationStatus {
    PENDING,
    IN_PREPARATION,
    PREPARED,
    DISCREPANCY
}

enum class StopStatus {
    PENDING,
    IN_PROGRESS,
    COMPLETED,
    PARTIAL,
    FAILED,

    /** Reserved for future policy; not exposed as a driver action in Phase 1. */
    SKIPPED
}

enum class OrderDeliveryStatus {
    READY_FOR_DELIVERY,
    DELIVERED,
    PARTIALLY_DELIVERED,
    FAILED,
    REFUSED
}

enum class DeliveryEventType {
    SHIFT_STARTED,
    ORDER_DELIVERED,
    ORDER_PARTIALLY_DELIVERED,
    ORDER_FAILED,
    ORDER_REFUSED,
    SHIFT_COMPLETED
}

enum class SyncStatus {
    PENDING,
    SYNCED,
    FAILED
}

enum class StartShiftBlockReason {
    MISSING_ROUTE_SNAPSHOT,
    INVALID_ROUTE_STATUS,
    ROUTE_ALREADY_COMPLETED,
    MISSING_DRIVER_SESSION,
    DRIVER_ASSIGNMENT_MISMATCH,
    WRONG_SERVICE_DATE,
    FINALIZATION_NOT_BEFORE_SERVICE_DATE,
    DOWNLOAD_NOT_BEFORE_SERVICE_DATE,
    DOWNLOAD_BEFORE_FINALIZATION,
    MISSING_MANIFEST_SNAPSHOT,
    MANIFEST_NOT_PREPARED,
    MANIFEST_ROUTE_MISMATCH,
    SNAPSHOT_METADATA_MISMATCH,
    SNAPSHOT_INCOMPLETE,
    MISSING_WAREHOUSE_PREPARATION_STATE,
    MISSING_STOPS,
    STOP_WITHOUT_ORDERS,
    ORDER_WITHOUT_LINES,
    INVALID_ORDERED_QUANTITY,
    INVALID_EXPECTED_MANIFEST_QUANTITY,
    INVALID_PREPARED_QUANTITY,
    NON_CONTIGUOUS_STOP_SEQUENCE,
    CHECKSUM_MISMATCH
}

/** Reason values below are a Phase 1 mock catalogue, not approved production policy. */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class MockOnly

@MockOnly
enum class MockDeliveryReasonCode(
    val requiresNote: Boolean = false
) {
    CUSTOMER_UNAVAILABLE,
    CUSTOMER_REFUSED_ORDER,
    PARTIAL_ACCEPTANCE_BY_PHARMACY,
    DAMAGED_OR_DISCREPANCY_AT_HANDOFF,
    OTHER(requiresNote = true)
}
