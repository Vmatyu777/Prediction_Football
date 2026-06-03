package com.predictionfootball.app.network

import com.predictionfootball.app.models.AuthTokenDto
import com.predictionfootball.app.models.AuthUserDto
import com.predictionfootball.app.models.LoginRequestDto
import com.predictionfootball.app.models.PredictionHistoryDto
import com.predictionfootball.app.models.PredictionHistoryUnreadCountDto
import com.predictionfootball.app.models.PredictionHistoryViewedDto
import com.predictionfootball.app.models.RegisterRequestDto

class AuthRepository(
    private val api: PredictionApiService = RetrofitClient.create(),
) {
    suspend fun register(username: String, email: String, password: String): AuthUserDto {
        return api.register(RegisterRequestDto(username = username, email = email, password = password))
    }

    suspend fun login(usernameOrEmail: String, password: String): AuthTokenDto {
        val response = api.login(LoginRequestDto(usernameOrEmail = usernameOrEmail, password = password))
        AuthTokenStore.saveAccessToken(response.accessToken)
        return response
    }

    suspend fun me(): AuthUserDto = api.me()

    suspend fun history(): List<PredictionHistoryDto> = api.history()

    suspend fun historyUnreadCount(): PredictionHistoryUnreadCountDto = api.historyUnreadCount()

    suspend fun markHistoryViewed(): PredictionHistoryViewedDto = api.markHistoryViewed()

    fun logout() {
        AuthTokenStore.clearAccessToken()
    }
}
