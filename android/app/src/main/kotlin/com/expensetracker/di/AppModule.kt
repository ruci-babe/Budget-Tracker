package com.expensetracker.di

import android.content.Context
import com.expensetracker.data.remote.RetrofitClient
import com.expensetracker.data.repository.ExpenseTrackerRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt dependency injection module
 * Provides singleton instances of API and repository objects
 */
@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    /**
     * Provide ExpenseTrackerRepository as singleton
     */
    @Singleton
    @Provides
    fun provideExpenseTrackerRepository(
        @ApplicationContext context: Context
    ): ExpenseTrackerRepository {
        RetrofitClient.initialize(context)
        return ExpenseTrackerRepository(context)
    }

    /**
     * Provide application context
     */
    @Singleton
    @Provides
    fun provideApplicationContext(@ApplicationContext context: Context): Context {
        return context
    }
}
