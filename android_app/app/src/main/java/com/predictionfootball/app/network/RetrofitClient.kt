package com.predictionfootball.app.network

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.predictionfootball.app.BuildConfig
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit

object RetrofitClient {
    private val json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
    }

    fun create(baseUrl: String = BuildConfig.API_BASE_URL): PredictionApiService {
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BASIC
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val token = AuthTokenStore.getAccessToken()
                val originalRequest = chain.request()
                val requestPath = originalRequest.url.encodedPath.trimStart('/')
                val shouldAttachToken = requestPath == "auth/me" ||
                    requestPath == "users/me/history" ||
                    requestPath.matches(Regex("^predict/\\d+$"))
                val request = if (token != null && shouldAttachToken) {
                    originalRequest
                        .newBuilder()
                        .addHeader("Authorization", "Bearer $token")
                        .build()
                } else {
                    originalRequest
                }
                val response = chain.proceed(request)
                if (shouldAttachToken && (response.code == 401 || response.code == 403)) {
                    AuthTokenStore.clearAccessToken()
                }
                response
            }
            .addInterceptor(logging)
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(PredictionApiService::class.java)
    }
}
