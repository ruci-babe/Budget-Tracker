# Expense Tracker - Android Mobile App

This is the Android mobile app for the Expense Tracker project. It allows users to:
- 📱 Add expenses on the go
- 📸 Capture receipt photos
- 🔄 Sync expenses with desktop and other devices
- 📊 View spending summaries
- 🏷️ Categorize expenses in real-time

## Project Status

🚧 **In Active Development** - Foundation and API client complete, UI development in progress

## Architecture Overview

The app follows **Clean Architecture** principles:

```
Presentation Layer (UI)
    ↓ (ViewModel)
Domain Layer (Use Cases)
    ↓ (Repository)
Data Layer (API, Database)
```

**Technology Stack:**
- **Language**: Kotlin
- **UI Framework**: Jetpack Compose (Modern declarative UI)
- **Networking**: Retrofit + OkHttp
- **Local Database**: Room
- **Dependency Injection**: Hilt
- **Preferences**: DataStore
- **Security**: EncryptedSharedPreferences, JWT Auth
- **Reactive**: Kotlin Coroutines + Flow
- **Logging**: Timber

## Project Structure

```
android/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── kotlin/com/expensetracker/
│   │       │   ├── data/
│   │       │   │   ├── remote/
│   │       │   │   │   ├── api/
│   │       │   │   │   │   └── ExpenseTrackerApi.kt          # Retrofit API interface
│   │       │   │   │   ├── dto/
│   │       │   │   │   │   └── ApiDtos.kt                    # Request/Response models
│   │       │   │   │   ├── interceptor/
│   │       │   │   │   │   └── AuthInterceptor.kt            # JWT authentication
│   │       │   │   │   └── RetrofitClient.kt                 # Retrofit setup
│   │       │   │   ├── repository/
│   │       │   │   │   └── ExpenseTrackerRepository.kt       # API wrapper
│   │       │   │   └── local/
│   │       │   │       └── (Room database - coming soon)
│   │       │   ├── domain/
│   │       │   │   ├── model/                                 # Business entities
│   │       │   │   └── usecase/                               # Use cases (coming soon)
│   │       │   ├── ui/
│   │       │   │   ├── MainActivity.kt
│   │       │   │   ├── viewmodel/
│   │       │   │   │   ├── AuthViewModel.kt                   # Auth screens
│   │       │   │   │   ├── ExpenseViewModel.kt                # Expense list
│   │       │   │   │   └── AddExpenseViewModel.kt             # Add expense
│   │       │   │   ├── screen/
│   │       │   │   │   ├── auth/
│   │       │   │   │   ├── home/
│   │       │   │   │   ├── expense/
│   │       │   │   │   └── settings/
│   │       │   │   └── theme/
│   │       │   │       └── Theme.kt                           # Material 3 theme
│   │       │   ├── di/
│   │       │   │   └── AppModule.kt                           # Hilt dependency injection
│   │       │   ├── util/
│   │       │   │   └── DateFormatter.kt                       # Utilities
│   │       │   └── ExpenseTrackerApp.kt                       # Application class
│   │       └── res/
│   │           ├── values/
│   │           │   └── strings.xml
│   │           └── drawable/
│   ├── build.gradle                                            # App-level gradle config
│   └── proguard-rules.pro
├── build.gradle                                                # Root gradle config
├── settings.gradle
└── gradle.properties
```

## API Client Implementation

### ✅ Completed Components

#### 1. **Retrofit API Interface** (`data/remote/api/ExpenseTrackerApi.kt`)
Defines all API endpoints:
```kotlin
interface ExpenseTrackerApi {
    @POST("auth/register")
    suspend fun registerUser(@Body request: RegisterRequest): Response<AuthResponse>
    
    @POST("transactions/sync")
    suspend fun syncTransactions(@Body request: SyncRequest): Response<SyncResponse>
    // ... more endpoints
}
```

#### 2. **Data Transfer Objects** (`data/remote/dto/ApiDtos.kt`)
Request/Response models for all API calls:
- `RegisterRequest`, `LoginRequest`
- `TransactionDTO`, `CategoryDTO`
- `SyncRequest`, `SyncResponse`
- `DeviceDTO`, `UserDTO`

#### 3. **JWT Authentication** (`data/remote/interceptor/AuthInterceptor.kt`)
- Automatically adds JWT token to all requests
- Stores/retrieves token from encrypted DataStore
- Token expiration detection
```kotlin
class AuthInterceptor(private val context: Context) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = getStoredToken()
        val request = chain.request()
            .newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()
        return chain.proceed(request)
    }
}
```

#### 4. **Retrofit Setup** (`data/remote/RetrofitClient.kt`)
- Configures OkHttp with interceptors
- Sets timeouts (30 seconds)
- Handles JSON serialization with Gson
- Singleton instance management

#### 5. **Repository Pattern** (`data/repository/ExpenseTrackerRepository.kt`)
Clean interface to API:
```kotlin
class ExpenseTrackerRepository(context: Context) {
    suspend fun login(username: String, password: String): Result<AuthResponse>
    suspend fun createTransaction(...): Result<TransactionDTO>
    suspend fun syncTransactions(...): Result<SyncResponse>
}
```

#### 6. **Hilt Dependency Injection** (`di/AppModule.kt`)
Provides singleton instances:
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Singleton
    @Provides
    fun provideExpenseTrackerRepository(context: Context): ExpenseTrackerRepository
}
```

## Quick Start

### Prerequisites
- Android Studio 2022.1+
- Android SDK 30+
- Kotlin 1.8+
- Java 17+

### Setup

1. **Clone/Extract the project**
```bash
cd android
```

2. **Configure Backend URL**

   Open `app/build.gradle` and update the backend URL:
   ```gradle
   buildTypes {
       debug {
           buildConfigField "String", "BACKEND_URL", '"http://10.0.2.2:5000"'  // Local emulator
       }
       release {
           buildConfigField "String", "BACKEND_URL", '"https://your-api.com"'  // Production
       }
   }
   ```

   **For different environments:**
   - **Emulator (local backend)**: `http://10.0.2.2:5000`
   - **On-device (local backend)**: `http://your-machine-ip:5000`
   - **Production**: Your deployed backend URL

3. **Open in Android Studio**
```bash
open -a "Android Studio" .
```
   Or: File → Open → Select `android` folder

4. **Build the project**
   - Allow Gradle sync to complete
   - Click "Build" → "Make Project"

5. **Run on Emulator/Device**
   - Click "Run" → "app"
   - Select target device/emulator
   - App launches with API client ready

## API Client Usage Examples

### In ViewModel (recommended pattern):

```kotlin
class AuthViewModel @Inject constructor(
    private val repository: ExpenseTrackerRepository
) : ViewModel() {
    
    fun login(username: String, password: String) {
        viewModelScope.launch {
            val result = repository.login(username, password)
            result.onSuccess { authResponse ->
                Timber.d("Login successful: ${authResponse.user.username}")
            }
            result.onFailure { error ->
                Timber.e(error, "Login failed")
            }
        }
    }
}
```

### API Calls with Error Handling:

```kotlin
// Repository handles all error/success logic
suspend fun getTransactions(): Result<TransactionsResponse> {
    return withContext(Dispatchers.IO) {
        try {
            val response = api.getTransactions(limit = 50)
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("API Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

## Backend Configuration

### Local Development

Start the backend server:
```bash
cd ../backend
pip install -r requirements.txt
python app.py  # Runs on http://localhost:5000
```

The app will connect using:
- **Emulator**: `http://10.0.2.2:5000`
- **Physical device**: `http://192.168.1.x:5000` (your machine IP)

### Production Deployment

Update `app/build.gradle`:
```gradle
release {
    buildConfigField "String", "BACKEND_URL", '"https://api.example.com"'
}
```

## Building & Running

### Run Debug APK
```bash
./gradlew installDebug
```

### Build Release APK
```bash
./gradlew assembleRelease
```

### Run Tests
```bash
./gradlew test
./gradlew connectedAndroidTest
```

### Check Dependencies
```bash
./gradlew dependencies
```

## Current Implementation Status

✅ **Complete:**
- Retrofit API client setup
- JWT authentication interceptor
- Repository pattern
- Hilt dependency injection
- App structure with Compose
- Error handling
- Timber logging

🚧 **In Progress:**
- Authentication UI screens (Login/Register)
- Expense list screen
- Add/edit expense screens

📋 **Planned:**
- Room local database
- Background sync service
- Receipt photo capture
- Offline transaction queue
- Conflict resolution
- Category management UI
- Settings screen

## Development Workflow

### When Backend Changes:

1. Update `ExpenseTrackerApi` interface if endpoints changed
2. Update DTOs in `ApiDtos.kt` if request/response format changed
3. Update `ExpenseTrackerRepository` if business logic changed
4. Unit tests for new endpoints

### Adding New API Endpoint:

1. Add method to `ExpenseTrackerApi`:
```kotlin
@POST("categories/bulk")
suspend fun bulkCreateCategories(@Body categories: List<CreateCategoryRequest>): Response<List<CategoryDTO>>
```

2. Create DTO models if needed:
```kotlin
data class BulkCategoryResponse(val categories: List<CategoryDTO>)
```

3. Add method to `ExpenseTrackerRepository`:
```kotlin
suspend fun createCategoriesBulk(categories: List<CreateCategoryRequest>): Result<List<CategoryDTO>>
```

4. Use in ViewModel:
```kotlin
val result = repository.createCategoriesBulk(categoryList)
```

## Testing

### Unit Tests
```kotlin
@Test
fun testLoginSuccess() = runTest {
    val result = repository.login("user", "pass")
    assertTrue(result.isSuccess)
}
```

### Integration Tests
```kotlin
@Test
fun testFullAuthFlow() = runTest {
    // Register
    // Login
    // Create transaction
    // Verify sync
}
```

## Troubleshooting

### Build Issues

**Gradle sync fails:**
```bash
./gradlew clean
./gradlew build
```

**Dependencies not resolving:**
```bash
./gradlew --refresh-dependencies
```

### Runtime Issues

**Cannot connect to backend:**
- Check backend is running: `curl http://localhost:5000/health`
- Use correct IP for your setup (emulator vs device)
- Check firewall/network settings

**Token invalid errors:**
- Token expired - re-login
- Wrong backend URL - verify buildConfig
- CORS issues - check backend CORS settings

**Build errors:**
- Clear cache: `./gradlew clean`
- Check Java version: `java -version` (should be 17+)
- Update Android Studio to latest version

## Contributing

See [main README](../README.md) for contribution guidelines.

## Resources

- [Android Jetpack Compose Documentation](https://developer.android.com/jetpack/compose)
- [Retrofit Documentation](https://square.github.io/retrofit/)
- [Hilt Dependency Injection](https://developer.android.com/training/dependency-injection/hilt-android)
- [Room Database](https://developer.android.com/training/data-storage/room)
- [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-overview.html)
- [Material Design 3](https://m3.material.io/)

## Next Steps

1. **Implement UI Screens** - Login, Expense List, Add Expense
2. **Add Room Database** - Local transaction storage
3. **Background Sync** - WorkManager for automatic sync
4. **Photo Capture** - Camera integration for receipts
5. **Testing** - Unit and integration tests

---

For backend API documentation, see [../backend/README.md](../backend/README.md)

