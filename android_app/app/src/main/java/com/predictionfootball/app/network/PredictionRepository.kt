package com.predictionfootball.app.network

import com.predictionfootball.app.models.MatchDetailDto
import com.predictionfootball.app.models.MatchSummaryDto
import com.predictionfootball.app.models.PredictionDto

class PredictionRepository(
    private val api: PredictionApiService = RetrofitClient.create(),
) {
    suspend fun recentMatches(): List<MatchSummaryDto> = api.getSampledRecentMatches()

    suspend fun upcomingMatches(): List<MatchSummaryDto> = api.getUpcomingMatches()

    suspend fun showcaseMatches(): List<MatchSummaryDto> = api.getShowcaseMatches()

    suspend fun matchDetails(matchId: Long): MatchDetailDto = api.getMatchDetails(matchId)

    suspend fun generatePrediction(matchId: Long): PredictionDto = api.generatePrediction(matchId)
}
