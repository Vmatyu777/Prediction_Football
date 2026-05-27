package com.predictionfootball.app.network

import com.predictionfootball.app.models.MatchDetailDto
import com.predictionfootball.app.models.MatchSummaryDto
import com.predictionfootball.app.models.PredictionDto
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface PredictionApiService {
    @GET("matches/recent")
    suspend fun getRecentMatches(
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0,
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
