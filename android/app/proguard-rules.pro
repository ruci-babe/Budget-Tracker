# Retrofit
-keep class com.expensetracker.data.remote.dto.** { *; }
-keep interface com.expensetracker.data.remote.api.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.<Http>* <methods>;
}

# Gson
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer
-keepclassmembers,allowobfuscation class * {
  @com.google.gson.annotations.SerializedName <fields>;
}

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }

# Hilt
-keep class dagger.hilt.** { *; }
-keep class com.expensetracker.di.** { *; }
-keep class javax.inject.** { *; }

# Jetpack Compose
-keep class androidx.compose.** { *; }
-keep interface androidx.compose.** { *; }

# Keep all data classes
-keep class com.expensetracker.data.** { *; }
-keepclassmembers class com.expensetracker.data.** {
    <init>(...);
}

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep Timber
-keep class timber.log.** { *; }
