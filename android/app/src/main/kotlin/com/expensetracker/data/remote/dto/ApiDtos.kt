package com.expensetracker.data.remote.dto

import com.google.gson.annotations.SerializedName
import java.time.LocalDate
import java.time.LocalDateTime

// ==================== Auth DTOs ====================

data class RegisterRequest(
    val username: String,
    val email: String,
    val password: String
)

data class LoginRequest(
    val username: String,
    val password: String
)

data class AuthResponse(
    val message: String,
    val user: UserDTO,
    val token: String
)

// ==================== User DTOs ====================

data class UserDTO(
    val id: Int,
    val username: String,
    val email: String,
    val created_at: String,
    val last_sync: String?
)

// ==================== Device DTOs ====================

data class RegisterDeviceRequest(
    val device_name: String,
    val device_type: String,  // 'android', 'desktop', 'ios', 'web'
    val device_id: String     // UUID
)

data class DeviceDTO(
    val id: Int,
    val device_name: String,
    val device_type: String,
    val device_id: String,
    val last_seen: String,
    val created_at: String
)

// ==================== Category DTOs ====================

data class CategoryDTO(
    val id: Int,
    val name: String,
    val color: String,
    val icon: String?,
    val created_at: String,
    val updated_at: String
)

data class CreateCategoryRequest(
    val name: String,
    val color: String = "#2E86DE",
    val icon: String? = null
)

// ==================== Transaction DTOs ====================

data class TransactionDTO(
    val id: Int,
    val date: String,              // YYYY-MM-DD
    val description: String,
    val amount: Double,
    val vendor: String?,
    val category_id: Int?,
    val category_name: String?,
    val payment_method: String?,   // 'cash', 'card', 'mobile', 'email', 'imported'
    val is_recurring: Boolean,
    val is_duplicate: Boolean,
    val receipt_image: String?,
    val notes: String?,
    val created_at: String,
    val updated_at: String,
    val synced_at: String?
)

data class CreateTransactionRequest(
    val date: String,              // YYYY-MM-DD
    val description: String,
    val amount: Double,
    val vendor: String? = null,
    val category_id: Int? = null,
    val payment_method: String = "card",
    val notes: String? = null,
    val receipt_image: String? = null
)

data class UpdateTransactionRequest(
    val date: String? = null,
    val description: String? = null,
    val amount: Double? = null,
    val vendor: String? = null,
    val category_id: Int? = null,
    val payment_method: String? = null,
    val notes: String? = null,
    val is_recurring: Boolean? = null,
    val is_duplicate: Boolean? = null
)

// ==================== Sync DTOs ====================

data class SyncRequest(
    val device_id: String,
    val transactions: List<CreateTransactionRequest>,
    val last_sync: String? = null
)

data class SyncResponse(
    val message: String,
    val items_synced: Int,
    val conflicts: Int,
    val server_timestamp: String
)

data class TransactionsResponse(
    val transactions: List<TransactionDTO>,
    val count: Int,
    val server_timestamp: String
)

data class SyncLogDTO(
    val id: Int,
    val sync_type: String,      // 'pull', 'push', 'full'
    val items_synced: Int,
    val conflicts: Int,
    val status: String,         // 'success', 'partial', 'failed'
    val error_message: String?,
    val synced_at: String
)

// ==================== Error/Response Wrappers ====================

data class ErrorResponse(
    val message: String,
    val status: Int? = null
)

data class ApiResponse<T>(
    val message: String? = null,
    val data: T? = null,
    val status: String? = null
)
