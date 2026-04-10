# Android API Client - Implementation Guide

## Overview

The Android app uses a complete API client implementation with:
- ✅ Retrofit for HTTP communication
- ✅ JWT authentication interceptor
- ✅ Repository pattern for clean architecture
- ✅ Error handling with Result wrapper
- ✅ Hilt dependency injection
- ✅ Secure token storage in DataStore

## Architecture Layers

```
UI Layer (Compose Screens)
    ↓ ViewModel
Domain Layer (Use Cases)
    ↓ Repository
Data Layer (API + Interceptors)
    ↓ Retrofit / OkHttp
Backend API
```

## API Endpoints Implemented (14 total)

### Authentication (2)
- `POST /auth/register` - Create new account
- `POST /auth/login` - Login and get JWT token

### Device Management (3)
- `POST /devices/register` - Register mobile device
- `GET /devices` - List registered devices
- `DELETE /devices/{id}` - Unregister device

### Categories (3)
- `GET /categories` - Get user's categories
- `POST /categories` - Create new category
- `PUT /categories/{id}` - Update category
- `DELETE /categories/{id}` - Delete category

### Transactions (4)
- `GET /transactions` - Get transaction list
- `POST /transactions` - Create transaction
- `PUT /transactions/{id}` - Update transaction
- `DELETE /transactions/{id}` - Delete transaction

### Sync (2)
- `POST /transactions/sync` - Sync transactions with server
- `GET /sync/logs` - Get sync history

### Health (1)
- `GET /health` - API health check

## Core Components

### 1. Retrofit API Interface

**File**: `data/remote/api/ExpenseTrackerApi.kt`

```kotlin
interface ExpenseTrackerApi {
    @POST("auth/register")
    suspend fun registerUser(@Body request: RegisterRequest): Response<AuthResponse>
    
    @POST("transactions/sync")
    suspend fun syncTransactions(@Body request: SyncRequest): Response<SyncResponse>
    // ... 12 more endpoints
}
```

**Features:**
- All functions are `suspend` (Kotlin Coroutines)
- Returns `Response<T>` for manual error handling
- Supports path parameters, query params, and request bodies
- Zero logic, pure API contract

### 2. Data Transfer Objects (DTOs)

**File**: `data/remote/dto/ApiDtos.kt`

```kotlin
// Request models
data class RegisterRequest(username: String, email: String, password: String)
data class CreateTransactionRequest(date: String, description: String, amount: Double)

// Response models
data class AuthResponse(val message: String, val user: UserDTO, val token: String)
data class TransactionDTO(val id: Int, val date: String, val amount: Double, ...)
```

**Features:**
- Using `@SerializedName` for JSON field mapping
- All fields properly typed (String, Int, Double, Boolean)
- Date strings in ISO format (YYYY-MM-DD)
- DTOs mirror backend schema exactly

### 3. JWT Authentication Interceptor

**File**: `data/remote/interceptor/AuthInterceptor.kt`

```kotlin
class AuthInterceptor(private val context: Context) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = runBlocking { TokenManager.getToken(context) }
        val request = chain.request()
            .newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()
        return chain.proceed(request)
    }
}
```

**Features:**
- Automatically adds `Authorization: Bearer {token}` to all requests
- Retrieves token from secure DataStore
- Runs synchronously (required for interceptor)
- Adds Content-Type header

**TokenManager Features:**
```kotlin
object TokenManager {
    suspend fun saveToken(context: Context, token: String)
    suspend fun getToken(context: Context): String?
    suspend fun clearToken(context: Context)
    fun isTokenExpired(token: String): Boolean  // Parses JWT expiry
}
```

### 4. Retrofit Client Setup

**File**: `data/remote/RetrofitClient.kt`

```kotlin
object RetrofitClient {
    fun initialize(context: Context) {
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(context))
            .addNetworkInterceptor(loggingInterceptor())
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()
        
        retrofit = Retrofit.Builder()
            .baseUrl(BuildConfig.BACKEND_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(okHttpClient)
            .build()
    }
    
    fun getApiService(): ExpenseTrackerApi
}
```

**Configuration:**
- Base URL: `BuildConfig.BACKEND_URL` (configurable per build type)
- Timeouts: 30 seconds
- JSON converter: Gson
- Logging: Network interceptor with Timber

### 5. Repository Pattern

**File**: `data/repository/ExpenseTrackerRepository.kt`

```kotlin
class ExpenseTrackerRepository(private val context: Context) {
    suspend fun login(username: String, password: String): Result<AuthResponse> {
        return try {
            val response = api.loginUser(LoginRequest(username, password))
            if (response.isSuccessful) {
                TokenManager.saveToken(context, response.body()!!.token)
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.message()))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

**Pattern Benefits:**
- Centralized error handling
- Automatic token management
- Clean separation from UI
- Easy to test and mock
- Consistent Result<T> wrapper

### 6. Hilt Dependency Injection

**File**: `di/AppModule.kt`

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Singleton
    @Provides
    fun provideExpenseTrackerRepository(
        @ApplicationContext context: Context
    ): ExpenseTrackerRepository {
        RetrofitClient.initialize(context)
        return ExpenseTrackerRepository(context)
    }
}
```

**Injection in ViewModel:**
```kotlin
class AuthViewModel @Inject constructor(
    private val repository: ExpenseTrackerRepository
) : ViewModel()
```

## Usage Patterns

### ✅ Recommended: Repository + ViewModel + Coroutines

```kotlin
class LoginViewModel @Inject constructor(
    private val repository: ExpenseTrackerRepository
) : ViewModel() {
    
    private val _loginState = MutableStateFlow<LoginState>(LoginState.Idle)
    val loginState: StateFlow<LoginState> = _loginState.asStateFlow()
    
    fun login(username: String, password: String) {
        viewModelScope.launch {
            _loginState.value = LoginState.Loading
            val result = repository.login(username, password)
            _loginState.value = result
                .fold(
                    onSuccess = { LoginState.Success(it) },
                    onFailure = { LoginState.Error(it.message ?: "Unknown error") }
                )
        }
    }
}

sealed class LoginState {
    object Idle : LoginState()
    object Loading : LoginState()
    data class Success(val response: AuthResponse) : LoginState()
    data class Error(val message: String) : LoginState()
}
```

### API Call with Error Handling

```kotlin
suspend fun getTransactions() {
    val result = repository.getTransactions(limit = 100)
    result
        .onSuccess { response ->
            Timber.d("Got ${response.transactions.size} transactions")
            // Update UI
        }
        .onFailure { error ->
            Timber.e(error, "Failed to fetch transactions")
            // Show error to user
        }
}
```

### Syncing Transactions

```kotlin
suspend fun syncExpenses() {
    val transactions = localDatabase.getAllUnsyncedTransactions()
    val deviceId = TokenManager.getDeviceId(context)
    
    val result = repository.syncTransactions(
        deviceId = deviceId!!,
        transactions = transactions.map { it.toDTO() }
    )
    
    if (result.isSuccess) {
        val syncResponse = result.getOrNull()
        Timber.d("Synced ${syncResponse?.items_synced} items")
        localDatabase.markAsSynced(syncResponse.server_timestamp)
    }
}
```

## Configuration

### Backend URL

**For Local Development (Emulator):**
```gradle
debug {
    buildConfigField "String", "BACKEND_URL", '"http://10.0.2.2:5000"'
}
```

**For Local Development (Physical Device):**
```gradle
debug {
    buildConfigField "String", "BACKEND_URL", '"http://192.168.1.100:5000"'
}
```
(Replace IP with your machine's IP)

**For Production:**
```gradle
release {
    buildConfigField "String", "BACKEND_URL", '"https://api.example.com"'
}
```

## Request/Response Examples

### Register User

**Request:**
```http
POST /auth/register HTTP/1.1
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secure_password_123"
}
```

**Response (Success):**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2026-04-10T12:00:00",
    "last_sync": null
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE2NDk2MjAwMDB9.signature"
}
```

### Sync Transactions

**Request:**
```http
POST /transactions/sync HTTP/1.1
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "device_id": "android-uuid-12345",
  "transactions": [
    {
      "date": "2026-04-10",
      "description": "Coffee at Starbucks",
      "amount": 5.50,
      "vendor": "Starbucks",
      "payment_method": "card",
      "notes": null,
      "receipt_image": null
    }
  ],
  "last_sync": "2026-04-09T18:30:00"
}
```

**Response (Success):**
```json
{
  "message": "Sync successful",
  "items_synced": 1,
  "conflicts": 0,
  "server_timestamp": "2026-04-10T13:45:30"
}
```

## Error Handling

### Common HTTP Errors

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Unauthorized (token invalid) | Re-login user |
| 403 | Forbidden | Check permissions |
| 404 | Not found | Handle gracefully |
| 500 | Server error | Retry with backoff |

### Network Errors

```kotlin
try {
    val result = repository.login(username, password)
} catch (e: SocketTimeoutException) {
    // Network timeout - retry or show message
} catch (e: ConnectException) {
    // Cannot connect to server
} catch (e: IOException) {
    // Network I/O error
} catch (e: Exception) {
    // Other errors
}
```

## Security Considerations

✅ **Implemented:**
- JWT tokens in secure DataStore (encrypted)
- HTTPS-ready configuration
- Token expiration checking
- Auto-logout on token expiry

⚠️ **To Implement:**
- SSL pinning
- Request signing
- Rate limiting on client side
- Biometric auth for tokens

## Testing

### Mocking Repository

```kotlin
@Test
fun testLoginSuccess() = runTest {
    // Mock
    val mockRepository = mockk<ExpenseTrackerRepository>()
    coEvery { mockRepository.login("user", "pass") } returns 
        Result.success(AuthResponse(...))
    
    // Test
    val viewModel = AuthViewModel(mockRepository)
    viewModel.login("user", "pass")
    
    assert(viewModel.loginState.value is LoginState.Success)
}
```

### Integration Testing

```kotlin
@Test
fun testEndToEndLogin() = runTest {
    RetrofitClient.initialize(context)
    val repository = ExpenseTrackerRepository(context)
    
    val result = repository.register(
        "testuser", 
        "test@example.com", 
        "password"
    )
    
    assertTrue(result.isSuccess)
}
```

## Troubleshooting

### Issue: "Cannot resolve symbol 'BuildConfig'"
**Solution:** Build the app once (`./gradlew build`)

### Issue: "MissingKotlinMetadataException"
**Solution:** Invalidate caches (File → Invalidate Caches)

### Issue: "SSL: CERTIFICATE_VERIFY_FAILED"
**Solution:** In development, allow cleartext:
```xml
<!-- android/app/src/main/res/xml/network_security_config.xml -->
<domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="true">10.0.2.2</domain>
</domain-config>
```

### Issue: "401 Unauthorized" on all requests
**Solution:** Check token in Logcat, verify login success first

## Performance Tips

- Use `withContext(Dispatchers.IO)` for API calls
- Cache responses in local database
- Implement request retry with exponential backoff
- Use View Binding instead of findViewById
- Profile with Android Profiler

## Next Steps

1. Implement Room database for local storage
2. Create UI screens using Compose
3. Implement background sync with WorkManager
4. Add unit and integration tests
5. Implement offline-first architecture
