package com.expensetracker.data.remote.interceptor

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking
import okhttp3.*
import okhttp3.logging.HttpLoggingInterceptor
import timber.log.Timber

private val Context.dataStore by preferencesDataStore(name = "auth_preferences")
private val JWT_TOKEN_KEY = stringPreferencesKey("jwt_token")
private val DEVICE_ID_KEY = stringPreferencesKey("device_id")

/**
 * Interceptor that adds JWT authentication token to all requests
 */
class AuthInterceptor(private val context: Context) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var request = chain.request()

        // Get token from DataStore (synchronously for interceptor)
        val token = runBlocking {
            context.dataStore.data.map { preferences ->
                preferences[JWT_TOKEN_KEY]
            }.first()
        }

        // Add Authorization header if token exists
        if (!token.isNullOrEmpty()) {
            request = request.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .addHeader("Content-Type", "application/json")
                .build()
        }

        return chain.proceed(request)
    }
}

/**
 * Logging interceptor for debugging API calls
 */
fun loggingInterceptor(): HttpLoggingInterceptor {
    return HttpLoggingInterceptor { message ->
        Timber.tag("OkHttp").d(message)
    }.apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
}

/**
 * Helper object for managing authentication tokens
 */
object TokenManager {
    suspend fun saveToken(context: Context, token: String) {
        context.dataStore.edit { preferences ->
            preferences[JWT_TOKEN_KEY] = token
        }
    }

    suspend fun getToken(context: Context): String? {
        return context.dataStore.data.map { preferences ->
            preferences[JWT_TOKEN_KEY]
        }.first()
    }

    suspend fun clearToken(context: Context) {
        context.dataStore.edit { preferences ->
            preferences.remove(JWT_TOKEN_KEY)
        }
    }

    suspend fun saveDeviceId(context: Context, deviceId: String) {
        context.dataStore.edit { preferences ->
            preferences[DEVICE_ID_KEY] = deviceId
        }
    }

    suspend fun getDeviceId(context: Context): String? {
        return context.dataStore.data.map { preferences ->
            preferences[DEVICE_ID_KEY]
        }.first()
    }

    fun isTokenExpired(token: String): Boolean {
        return try {
            val parts = token.split(".")
            if (parts.size != 3) return true

            val payload = parts[1]
            val decoded = String(android.util.Base64.decode(payload, android.util.Base64.DEFAULT))
            val exp = decoded.substringAfterLast("\"exp\":").substringBefore(",").toLongOrNull()

            if (exp != null) {
                val currentTime = System.currentTimeMillis() / 1000
                exp < currentTime
            } else {
                true
            }
        } catch (e: Exception) {
            Timber.e(e, "Error checking token expiration")
            true
        }
    }
}
