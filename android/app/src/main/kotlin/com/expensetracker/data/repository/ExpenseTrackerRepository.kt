package com.expensetracker.data.repository

import android.content.Context
import com.expensetracker.data.remote.RetrofitClient
import com.expensetracker.data.remote.dto.*
import com.expensetracker.data.remote.interceptor.TokenManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import timber.log.Timber

/**
 * Repository for handling all API calls
 * Provides clean interface separated from ViewModels
 */
class ExpenseTrackerRepository(private val context: Context) {
    private val api = RetrofitClient.getApiService()

    // ==================== Authentication ====================

    suspend fun register(
        username: String,
        email: String,
        password: String
    ): Result<AuthResponse> = withContext(Dispatchers.IO) {
        try {
            val request = RegisterRequest(username, email, password)
            val response = api.registerUser(request)
            if (response.isSuccessful && response.body() != null) {
                val authResponse = response.body()!!
                TokenManager.saveToken(context, authResponse.token)
                Result.success(authResponse)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Register error")
            Result.failure(e)
        }
    }

    suspend fun login(
        username: String,
        password: String
    ): Result<AuthResponse> = withContext(Dispatchers.IO) {
        try {
            val request = LoginRequest(username, password)
            val response = api.loginUser(request)
            if (response.isSuccessful && response.body() != null) {
                val authResponse = response.body()!!
                TokenManager.saveToken(context, authResponse.token)
                Result.success(authResponse)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Login error")
            Result.failure(e)
        }
    }

    suspend fun logout(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            TokenManager.clearToken(context)
            RetrofitClient.reset()
            Result.success(Unit)
        } catch (e: Exception) {
            Timber.e(e, "Logout error")
            Result.failure(e)
        }
    }

    // ==================== Device Management ====================

    suspend fun registerDevice(
        deviceName: String,
        deviceType: String,
        deviceId: String
    ): Result<DeviceDTO> = withContext(Dispatchers.IO) {
        try {
            val request = RegisterDeviceRequest(deviceName, deviceType, deviceId)
            val response = api.registerDevice(request)
            if (response.isSuccessful && response.body() != null) {
                TokenManager.saveDeviceId(context, deviceId)
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Register device error")
            Result.failure(e)
        }
    }

    // ==================== Categories ====================

    suspend fun getCategories(): Result<List<CategoryDTO>> = withContext(Dispatchers.IO) {
        try {
            val response = api.getCategories()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Get categories error")
            Result.failure(e)
        }
    }

    suspend fun createCategory(
        name: String,
        color: String = "#2E86DE",
        icon: String? = null
    ): Result<CategoryDTO> = withContext(Dispatchers.IO) {
        try {
            val request = CreateCategoryRequest(name, color, icon)
            val response = api.createCategory(request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Create category error")
            Result.failure(e)
        }
    }

    // ==================== Transactions ====================

    suspend fun getTransactions(since: String? = null, limit: Int = 100): Result<TransactionsResponse> =
        withContext(Dispatchers.IO) {
            try {
                val response = api.getTransactions(since, limit)
                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!)
                } else {
                    Result.failure(Exception(response.message()))
                }
            } catch (e: Exception) {
                Timber.e(e, "Get transactions error")
                Result.failure(e)
            }
        }

    suspend fun createTransaction(
        date: String,
        description: String,
        amount: Double,
        vendor: String? = null,
        categoryId: Int? = null,
        paymentMethod: String = "card",
        notes: String? = null,
        receiptImage: String? = null
    ): Result<TransactionDTO> = withContext(Dispatchers.IO) {
        try {
            val request = CreateTransactionRequest(
                date, description, amount, vendor, categoryId, paymentMethod, notes, receiptImage
            )
            val response = api.createTransaction(request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Create transaction error")
            Result.failure(e)
        }
    }

    suspend fun updateTransaction(
        transactionId: Int,
        date: String? = null,
        description: String? = null,
        amount: Double? = null,
        vendor: String? = null,
        categoryId: Int? = null,
        paymentMethod: String? = null,
        notes: String? = null,
        isRecurring: Boolean? = null,
        isDuplicate: Boolean? = null
    ): Result<TransactionDTO> = withContext(Dispatchers.IO) {
        try {
            val request = UpdateTransactionRequest(
                date, description, amount, vendor, categoryId, paymentMethod, notes, isRecurring, isDuplicate
            )
            val response = api.updateTransaction(transactionId, request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Update transaction error")
            Result.failure(e)
        }
    }

    suspend fun deleteTransaction(transactionId: Int): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val response = api.deleteTransaction(transactionId)
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Delete transaction error")
            Result.failure(e)
        }
    }

    // ==================== Sync ====================

    suspend fun syncTransactions(
        deviceId: String,
        transactions: List<CreateTransactionRequest>,
        lastSync: String? = null
    ): Result<SyncResponse> = withContext(Dispatchers.IO) {
        try {
            val request = SyncRequest(deviceId, transactions, lastSync)
            val response = api.syncTransactions(request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Sync transactions error")
            Result.failure(e)
        }
    }

    suspend fun healthCheck(): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val response = api.healthCheck()
            if (response.isSuccessful) {
                Result.success(true)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Timber.e(e, "Health check error")
            Result.failure(e)
        }
    }
}
