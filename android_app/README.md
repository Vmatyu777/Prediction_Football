# Prediction Football Android App

Android tablet MVP client for the existing FastAPI backend in this monorepo.

## Scope

The Android application is a thin client. It must not train models, generate ML features, access PostgreSQL/SQLite directly, use Room, or implement the reconciliation layer locally. Final prediction logic stays in the backend:

- match browsing: `GET /matches`, `GET /matches/{match_id}`, `GET /matches/upcoming`, `GET /matches/recent`, `GET /matches/recent/sampled`, `GET /matches/showcase`;
- prediction: `POST /predict/{match_id}`;
- stored prediction details: `GET /predictions/{prediction_id}`;
- auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`;
- authenticated history: `GET /users/me/history`, `GET /users/me/history/unread-count`, `POST /users/me/history/mark-viewed`;
- metadata and diagnostics: `GET /models`, `GET /health`, `GET /db/health`.

Repeated prediction requests are deduplicated by the backend for the same `match_id` and deployed outcome `model_id`. Android can safely call `POST /predict/{match_id}` again without creating duplicate prediction characteristic rows for the same deployed model.

Authenticated prediction requests add rows to `user_query_history`. This table stores user actions, so repeated requests can create multiple rows for the same stored prediction. The backend stores the user's history marker in `users.last_history_viewed_at`; `GET /users/me/history/unread-count` counts distinct prediction IDs newer than that marker, and `POST /users/me/history/mark-viewed` advances it after History has loaded. The Android history screen sorts by `query_date` descending and shows only the latest row per `prediction_id`.

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
- `ui/components`: shared dark cards, loading skeletons, floating notifications, status badges, probability bars, and action components.
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
- Login/Register: FastAPI auth flow with validation, floating in-app error notifications, and show/hide password controls.
- Match List: Recent/Upcoming/Best Predictions switch plus league and season filters with `All`; the screen opens on Upcoming, caches loaded tabs in `MatchListViewModel`, refreshes stale cached tabs in the background after the client-side TTL expires, and shows the last successful update time for the active tab.
- Match Details: teams, league, date, status, result if available, latest odds, and compact tablet layout.
- Prediction Result: final reconciled prediction from `POST /predict/{match_id}` in a dark analytics dashboard style.
- Profile: current user details in a dashboard-style card, smooth unread-history badge on the History action, stable fallback for non-auth profile loading problems, and logout.
- History: latest visible row per `prediction_id`, prepared loading before first render, scroll-to-top on open, temporary highlight for newly viewed prediction rows, prediction characteristics, and comparison with factual result when the match is finished.

For tablet layout, prefer a list-detail layout on wide screens:

- left pane: match list and filters;
- right pane: selected match details and prediction result;
- single-pane navigation for narrower emulator profiles.

## Adaptive Layout Status

The Android app remains tablet-first. Basic phone support has been improved without adding a separate adaptive architecture:

- The completed UI redesign uses a dark football analytics theme with near-black backgrounds, dark cards, and lime accents for CTAs, statuses, prediction highlights, and progress bars.
- Login and Register preserve non-password input in `AuthViewModel`; password values stay local to the Compose screen and are not stored in the ViewModel.
- Login and Register are vertically scrollable, use IME padding so the keyboard does not hide form controls, and show floating in-app notifications instead of system Toasts.
- Match Details, Prediction Result, and Profile are vertically scrollable where needed to avoid clipped content on phones and landscape-sized heights.
- Match Details has a more compact tablet layout; Prediction Result and History use dark sports analytics cards; Profile uses a centered dashboard-style user card with an unread-history badge.
- Prediction Result uses one column for prediction metric cards on narrow screens and keeps two columns on wider tablet screens.
- Match List tabs and filters are horizontally scrollable on narrow screens.
- History is loaded before the list is shown to avoid visually inserting a new top row after the screen is already visible. New rows are highlighted by `prediction_id` for 5 seconds with a background/border animation; scrolling does not clear highlight state.
- Actual upcoming matches and seeded demo matches are visually separated. Demo matches use a compact `Демо` badge.

Full adaptive behavior is not implemented yet. The app does not use `WindowSizeClass`, tablet master-detail navigation, or landscape-specific layouts. These remain post-MVP improvements.

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

    @GET("users/me/history/unread-count")
    suspend fun historyUnreadCount(): PredictionHistoryUnreadCountDto

    @POST("users/me/history/mark-viewed")
    suspend fun markHistoryViewed(): PredictionHistoryViewedDto

    @GET("matches/upcoming")
    suspend fun getUpcomingMatches(...): List<MatchSummaryDto>

    @GET("matches/recent/sampled")
    suspend fun getRecentMatches(...): List<MatchSummaryDto>

    @GET("matches/showcase")
    suspend fun getShowcaseMatches(...): List<MatchSummaryDto>

    @GET("matches/{match_id}")
    suspend fun getMatchDetails(@Path("match_id") matchId: Long): MatchDetailDto

    @POST("predict/{match_id}")
    suspend fun generatePrediction(@Path("match_id") matchId: Long): PredictionDto
}
```

The backend can return technical values such as `H`, `D`, `A`, `Yes`, `No`, `Finished`, `Market Average`, or match sources such as `historical`, `demo`, and `api`. Android keeps these values unchanged in DTOs and maps them only in the UI layer to Russian user-facing labels. Prediction outcomes use full labels in the result screen; `historical` source labels are hidden, while `demo` and `api` are shown as demo/API match labels.

The Examples tab uses `GET /matches/showcase`. It shows historical matches selected for demonstration because existing model predictions matched the factual result well. It is separate from Recent matches and does not replace aggregate model-quality metrics.

Backend `prediction.created_at` values are stored as UTC. Android treats `created_at` as UTC and displays it in the local timezone of the emulator or physical tablet. The device timezone affects display only.

Auth token flow:

- login stores the JWT access token in `SharedPreferences`;
- Retrofit/OkHttp adds `Authorization: Bearer <token>` outside composables;
- Splash validates the token through `/auth/me`;
- `401` or `403` clears the token and returns the user to login;
- logout clears the token and resets the navigation stack through a known start destination with `launchSingleTop`;
- profile fallback is shown only for non-auth profile loading problems; logout and session-expired flows navigate to Login without showing the fallback card.

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

VPS backend:

```text
https://prediction-football.ru/
```

The root URL serves a small backend landing page. Verify production availability before building an APK:

```bash
curl https://prediction-football.ru/
curl https://prediction-football.ru/health
```

The Android client remains a thin API client and should use the HTTPS production base URL for deployed builds. Backend landing pages and browser-only HTML 404 pages are not part of the Android API flow; API clients continue to receive JSON error responses.

Build a debug APK against the VPS backend:

```bash
./gradlew :app:assembleDebug -PapiBaseUrl=https://prediction-football.ru/
```

Install the VPS-targeted debug build on a connected emulator or device:

```bash
./gradlew :app:installDebug -PapiBaseUrl=https://prediction-football.ru/
```

Run backend for emulator/device testing:

```bash
cd ..
cp .env.example .env
docker compose up -d --build
```

The Docker Compose stack starts PostgreSQL and the FastAPI backend. The backend container listens on `0.0.0.0:8000`, so Android Emulator can use `http://10.0.2.2:8000/` and a physical tablet can use `http://<LAN_IP>:8000/`.

If you run the backend directly on the host instead of the backend container, start PostgreSQL first and then run Uvicorn:

```bash
cd ..
cp .env.example .env
docker compose up -d postgres
python src/api/database/init_db.py
python src/api/database/seed_db.py
python src/api/database/seed_final_models.py
python src/api/database/load_football_data.py
python src/api/database/load_elo_ratings.py
python src/api/database/seed_demo_upcoming_matches.py
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

PostgreSQL 16 through Docker Compose is the primary production-like backend database mode. SQLite remains a backend-only legacy/local fallback when `DATABASE_URL` is not set. The `.env.example` file is the tracked template; `.env` is local and must not be committed. Verify backend database connectivity with `GET /db/health`; in PostgreSQL mode it should return `database=postgresql`.

For local Android emulator only, `--host 127.0.0.1` also works with `10.0.2.2`, but `0.0.0.0` is more convenient when testing on a real tablet.

Build the app from this directory:

```bash
./gradlew :app:assembleDebug
```

On Windows command line, if `java` is not available in `PATH`, use the Android Studio JBR for the current PowerShell session:

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"
.\gradlew.bat :app:assembleDebug -PapiBaseUrl=https://prediction-football.ru/
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

For the deployed VPS backend, rebuild with:

```bash
./gradlew :app:assembleDebug -PapiBaseUrl=https://prediction-football.ru/
```

## MVP Constraints

Not included in the initial mobile layer:

- advanced authentication;
- email verification;
- password reset;
- Room database;
- persistent local caching;
- push notifications;
- background sync;
- team/league logos;
- standings, H2H, calendar, and news screens;
- local ML inference;
- direct SQLite access.

These can be added later after the FastAPI contract and MVP screen flow are stable.
