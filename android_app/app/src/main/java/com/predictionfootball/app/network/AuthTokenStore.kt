package com.predictionfootball.app.network

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object AuthTokenStore {
    private const val FILE_NAME = "auth_session"
    private const val ACCESS_TOKEN_KEY = "access_token"

    private lateinit var appContext: Context
    private val _isAuthenticated = MutableStateFlow(false)
    val isAuthenticated: StateFlow<Boolean> = _isAuthenticated.asStateFlow()

    fun initialize(context: Context) {
        appContext = context.applicationContext
        _isAuthenticated.value = getAccessToken() != null
    }

    fun getAccessToken(): String? {
        check(::appContext.isInitialized) { "AuthTokenStore is not initialized" }
        return appContext
            .getSharedPreferences(FILE_NAME, Context.MODE_PRIVATE)
            .getString(ACCESS_TOKEN_KEY, null)
    }

    fun saveAccessToken(token: String) {
        check(::appContext.isInitialized) { "AuthTokenStore is not initialized" }
        appContext
            .getSharedPreferences(FILE_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(ACCESS_TOKEN_KEY, token)
            .apply()
        _isAuthenticated.value = true
    }

    fun clearAccessToken() {
        check(::appContext.isInitialized) { "AuthTokenStore is not initialized" }
        appContext
            .getSharedPreferences(FILE_NAME, Context.MODE_PRIVATE)
            .edit()
            .remove(ACCESS_TOKEN_KEY)
            .apply()
        _isAuthenticated.value = false
    }
}
