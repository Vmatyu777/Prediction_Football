package com.predictionfootball.app.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class RegisterRequestDto(
    val username: String,
    val email: String,
    val password: String,
)

@Serializable
data class LoginRequestDto(
    @SerialName("username_or_email") val usernameOrEmail: String,
    val password: String,
)

@Serializable
data class AuthUserDto(
    val id: Long,
    val username: String,
    val email: String,
    val role: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class AuthTokenDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("token_type") val tokenType: String,
    val user: AuthUserDto,
)

@Serializable
data class PredictionHistoryDto(
    val id: Long,
    @SerialName("query_date") val queryDate: String,
    @SerialName("prediction_id") val predictionId: Long,
    @SerialName("match_id") val matchId: Long,
    @SerialName("match_date") val matchDate: String,
    val league: String,
    val season: String,
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    @SerialName("prediction_created_at") val predictionCreatedAt: String,
    val outcome: String,
    val btts: String? = null,
    val over25: String? = null,
    @SerialName("corners_over95") val cornersOver95: String? = null,
    @SerialName("yellow_cards_over35") val yellowCardsOver35: String? = null,
    @SerialName("exact_score") val exactScore: String? = null,
    val result: MatchResultDto? = null,
)
