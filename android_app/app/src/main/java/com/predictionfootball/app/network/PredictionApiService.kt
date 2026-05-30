package com.predictionfootball.app.network

import com.predictionfootball.app.models.AuthTokenDto
import com.predictionfootball.app.models.AuthUserDto
import com.predictionfootball.app.models.LoginRequestDto
import com.predictionfootball.app.models.MatchDetailDto
import com.predictionfootball.app.models.MatchSummaryDto
import com.predictionfootball.app.models.PredictionDto
import com.predictionfootball.app.models.PredictionHistoryDto
import com.predictionfootball.app.models.RegisterRequestDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface PredictionApiService {
    @POST("auth/register")
    suspend fun register(@Body request: RegisterRequestDto): AuthUserDto

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequestDto): AuthTokenDto

    @GET("auth/me")
    suspend fun me(): AuthUserDto

    @GET("users/me/history")
    suspend fun history(): List<PredictionHistoryDto>

    @GET("matches/recent")
    suspend fun getRecentMatches(
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0,
    ): List<MatchSummaryDto>

    @GET("matches/recent/sampled")
    suspend fun getSampledRecentMatches(
        @Query("per_league_season") perLeagueSeason: Int = 5,
    ): List<MatchSummaryDto>

    @GET("matches/upcoming")
    suspend fun getUpcomingMatches(
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0,
    ): List<MatchSummaryDto>

    @GET("matches/{match_id}")
    suspend fun getMatchDetails(
        @Path("match_id") matchId: Long,
    ): MatchDetailDto

    @POST("predict/{match_id}")
    suspend fun generatePrediction(
        @Path("match_id") matchId: Long,
    ): PredictionDto
}
