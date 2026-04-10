package com.expensetracker.data.remote.api

import com.expensetracker.data.remote.dto.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Retrofit API service for Expense Tracker backend
 * Handles all communication with the sync server
 */
interface ExpenseTrackerApi {

    // ==================== Authentication ====================

    @POST("auth/register")
    suspend fun registerUser(@Body request: RegisterRequest): Response<AuthResponse>

    @POST("auth/login")
    suspend fun loginUser(@Body request: LoginRequest): Response<AuthResponse>

    // ==================== Device Management ====================

    @POST("devices/register")
    suspend fun registerDevice(@Body request: RegisterDeviceRequest): Response<DeviceDTO>

    @GET("devices")
    suspend fun getDevices(): Response<List<DeviceDTO>>

    @DELETE("devices/{deviceId}")
    suspend fun unregisterDevice(@Path("deviceId") deviceId: Int): Response<Void>

    // ==================== Categories ====================

    @GET("categories")
    suspend fun getCategories(): Response<List<CategoryDTO>>

    @POST("categories")
    suspend fun createCategory(@Body request: CreateCategoryRequest): Response<CategoryDTO>

    @PUT("categories/{categoryId}")
    suspend fun updateCategory(
        @Path("categoryId") categoryId: Int,
        @Body request: CreateCategoryRequest
    ): Response<CategoryDTO>

    @DELETE("categories/{categoryId}")
    suspend fun deleteCategory(@Path("categoryId") categoryId: Int): Response<Void>

    // ==================== Transactions ====================

    @GET("transactions")
    suspend fun getTransactions(
        @Query("since") since: String? = null,
        @Query("limit") limit: Int = 100
    ): Response<TransactionsResponse>

    @GET("transactions/{transactionId}")
    suspend fun getTransaction(@Path("transactionId") transactionId: Int): Response<TransactionDTO>

    @POST("transactions")
    suspend fun createTransaction(@Body request: CreateTransactionRequest): Response<TransactionDTO>

    @PUT("transactions/{transactionId}")
    suspend fun updateTransaction(
        @Path("transactionId") transactionId: Int,
        @Body request: UpdateTransactionRequest
    ): Response<TransactionDTO>

    @DELETE("transactions/{transactionId}")
    suspend fun deleteTransaction(@Path("transactionId") transactionId: Int): Response<Void>

    // ==================== Sync ====================

    @POST("transactions/sync")
    suspend fun syncTransactions(@Body request: SyncRequest): Response<SyncResponse>

    @GET("sync/logs")
    suspend fun getSyncLogs(): Response<List<SyncLogDTO>>

    // ==================== Health Check ====================

    @GET("health")
    suspend fun healthCheck(): Response<Map<String, String>>
}
