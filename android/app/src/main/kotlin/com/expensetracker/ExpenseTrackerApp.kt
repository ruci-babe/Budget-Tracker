package com.expensetracker

import android.app.Application
import dagger.hilt.android.HiltAndroidApp
import timber.log.Timber

@HiltAndroidApp
class ExpenseTrackerApp : Application() {
    override fun onCreate() {
        super.onCreate()

        // Initialize Timber logging
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        } else {
            Timber.plant(CrashReportingTree())
        }

        Timber.d("Expense Tracker App initialized")
    }

    /**
     * Custom Timber tree for production crash reporting
     */
    private class CrashReportingTree : Timber.Tree() {
        override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
            // TODO: Send to crash reporting service (Firebase, Sentry, etc.)
            if (priority == android.util.Log.ERROR || priority == android.util.Log.WARN) {
                // Send to crash reporting
            }
        }
    }
}
