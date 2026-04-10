package com.expensetracker.data.remote

import android.content.Context
import com.expensetracker.BuildConfig
import com.expensetracker.data.remote.api.ExpenseTrackerApi
import com.expensetracker.data.remote.interceptor.AuthInterceptor
import com.expensetracker.data.remote.interceptor.loggingInterceptor
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Factory for creating Retrofit client and API service
 */
object RetrofitClient {
    private var retrofit: Retrofit? = null
    private var apiService: ExpenseTrackerApi? = null

    /**
     * Initialize Retrofit client with interceptors and configuration
     */
    fun initialize(context: Context) {
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(context))
            .addNetworkInterceptor(loggingInterceptor())
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()

        val gson: Gson = GsonBuilder()
            .setLenient()
            .create()

        retrofit = Retrofit.Builder()
            .baseUrl(BuildConfig.BACKEND_URL.ensureTrailingSlash())
            .addConverterFactory(GsonConverterFactory.create(gson))
            .client(okHttpClient)
            .build()

        apiService = retrofit?.create(ExpenseTrackerApi::class.java)
    }

    /**
     * Get the API service instance
     */
    fun getApiService(): ExpenseTrackerApi {
        return apiService ?: throw IllegalStateException(
            "RetrofitClient not initialized. Call initialize(context) first."
        )
    }

    /**
     * Get Retrofit instance
     */
    fun getRetrofit(): Retrofit {
        return retrofit ?: throw IllegalStateException(
            "RetrofitClient not initialized. Call initialize(context) first."
        )
    }

    /**
     * Reset the client (useful for logout)
     */
    fun reset() {
        retrofit = null
        apiService = null
    }

    private fun String.ensureTrailingSlash(): String {
        return if (endsWith("/")) this else "$this/"
    }
}
