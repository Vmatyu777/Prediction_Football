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
