# Prediction Football Android App

Android tablet MVP client for the existing FastAPI backend in this monorepo.

## Scope

The Android application is a thin client. It must not train models, generate ML features, access SQLite directly, or implement the reconciliation layer locally. Final prediction logic stays in the backend:

- match browsing: `GET /matches`, `GET /matches/{match_id}`, `GET /matches/upcoming`, `GET /matches/recent`;
- prediction: `POST /predict/{match_id}`;
- stored prediction details: `GET /predictions/{prediction_id}`;
- auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`;
- authenticated history: `GET /users/me/history`;
- metadata and diagnostics: `GET /models`, `GET /health`, `GET /db/health`.

Repeated prediction requests are deduplicated by the backend for the same `match_id` and deployed outcome `model_id`. Android can safely call `POST /predict/{match_id}` again without creating duplicate prediction characteristic rows for the same deployed model.

Authenticated prediction requests add rows to `user_query_history`. This table stores user actions, so repeated requests can create multiple rows for the same stored prediction. The Android history screen sorts by `query_date` descending and shows only the latest row per `prediction_id`.

## Android Studio Setup

Recommended options:

- New Project type: Empty Activity;
- Language: Kotlin;
- UI: Jetpack Compose;
- Minimum SDK: API 26 or newer;
- Build configuration: Kotlin DSL;
- Package name: `com.predictionfootball.app`;
- Open/import this folder as an existing Gradle project: `android_app/`.

This folder is an existing Gradle project with its own Gradle wrapper. Open/import `android_app/` in Android Studio and use the normal Run action after the FastAPI backend is running.

## Dependencies

MVP dependencies are declared in `gradle/libs.versions.toml` and `app/build.gradle.kts`:

- Jetpack Compose;
- Material3;
- Navigation Compose;
- Retrofit;
- OkHttp;
- kotlinx.serialization;
- ViewModel + lifecycle runtime.

## Package Structure

```text
com.predictionfootball.app
+-- models
+-- navigation
+-- network
+-- ui
    +-- components
    +-- screens
    +-- theme
+-- viewmodel
```

Recommended responsibilities:

- `models`: DTOs that mirror FastAPI response schemas.
- `network`: Retrofit client, service interface, auth token store, auth repository, and prediction repository.
- `ui/DisplayMappings.kt`: maps technical backend values to Russian user-facing labels.
- `navigation`: Compose navigation graph and route definitions.
- `ui/components`: shared cards, loading, error, and action components.
- `ui/screens`: screen-level composables for match list, match details, and prediction result.
- `ui/theme`: Material3 color, typography, and tablet layout tokens.
- `viewmodel`: simple MVP ViewModels and UI state.

## Initial Screens

MVP navigation:

```text
Splash -> Login/Register -> MatchList -> MatchDetails -> PredictionResult
MatchList -> Profile -> History
```

Screen goals:

- Splash: short startup screen that validates a stored token with `GET /auth/me`.
- Login/Register: FastAPI auth flow with validation and temporary Toast error messages.
- Match List: Recent/Upcoming switch plus league and season filters with `All`.
- Match Details: teams, league, date, status, result if available, latest odds.
- Prediction Result: final reconciled prediction from `POST /predict/{match_id}`.
- Profile: current user details and logout.
- History: latest visible row per `prediction_id`, prediction characteristics, and comparison with factual result when the match is finished.

For tablet layout, prefer a list-detail layout on wide screens:

- left pane: match list and filters;
- right pane: selected match details and prediction result;
- single-pane navigation for narrower emulator profiles.

## API Layer Recommendation

Implemented Retrofit service shape:

```kotlin
interface PredictionApiService {
    @POST("auth/register")
    suspend fun register(...): AuthUserDto

    @POST("auth/login")
    suspend fun login(...): AuthTokenDto

    @GET("auth/me")
    suspend fun me(): AuthUserDto

    @GET("users/me/history")
    suspend fun history(): List<PredictionHistoryDto>

    @GET("matches/upcoming")
    suspend fun getUpcomingMatches(...): List<MatchSummaryDto>

    @GET("matches/recent")
    suspend fun getRecentMatches(...): List<MatchSummaryDto>

    @GET("matches/{match_id}")
    suspend fun getMatchDetails(@Path("match_id") matchId: Long): MatchDetailDto

    @POST("predict/{match_id}")
    suspend fun generatePrediction(@Path("match_id") matchId: Long): PredictionDto
}
```

The backend can return technical values such as `H`, `D`, `A`, `Yes`, `No`, `Finished`, or `Market Average`. Android keeps these values unchanged in DTOs and maps them only in the UI layer to Russian user-facing labels.

Backend `prediction.created_at` values are stored as UTC. Android treats `created_at` as UTC and displays it in the local timezone of the emulator or physical tablet. The device timezone affects display only.

Auth token flow:

- login stores the JWT access token in `SharedPreferences`;
- Retrofit/OkHttp adds `Authorization: Bearer <token>` outside composables;
- Splash validates the token through `/auth/me`;
- `401` or `403` clears the token and returns the user to login;
- logout clears the token and resets the navigation stack.

Credential validation is duplicated client-side for UX and enforced server-side:

- username: only Latin letters, digits, `_`, and `-`;
- email: ASCII email format, no Cyrillic characters;
- password: at least 8 printable ASCII characters, at least one Latin letter, and at least one digit; special characters are allowed.

Emulator base URL:

```text
http://10.0.2.2:8000/
```

`10.0.2.2` is an Android Emulator-only alias for the host machine. It does not work on a physical tablet.

Physical device or tablet on the same network:

```text
http://<LAN_IP>:8000/
```

The default debug build uses the emulator URL through `BuildConfig.API_BASE_URL`. For a physical tablet, pass a local LAN backend URL at build time:

```bash
./gradlew :app:assembleDebug -PapiBaseUrl=http://192.168.1.10:8000/
```

Run backend for emulator/device testing:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

For local Android emulator only, `--host 127.0.0.1` also works with `10.0.2.2`, but `0.0.0.0` is more convenient when testing on a real tablet.

Build the app from this directory:

```bash
./gradlew :app:assembleDebug
```

Install on a running emulator:

```bash
./gradlew :app:installDebug
```

Android Studio Run:

1. Start the backend separately.
2. Open `android_app/` in Android Studio.
3. Select an emulator or physical tablet.
4. Press Run.

For a physical tablet, use the laptop LAN IP and rebuild with:

```bash
./gradlew :app:assembleDebug -PapiBaseUrl=http://<LAN_IP>:8000/
```

## MVP Constraints

Not included in the initial mobile layer:

- advanced authentication;
- Room database;
- local caching;
- notifications;
- background sync;
- local ML inference;
- direct SQLite access.

These can be added later after the FastAPI contract and MVP screen flow are stable.
