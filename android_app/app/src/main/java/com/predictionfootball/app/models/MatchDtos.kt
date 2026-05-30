package com.predictionfootball.app.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class MatchSummaryDto(
    val id: Long,
    @SerialName("match_date") val matchDate: String,
    val league: String,
    val season: String,
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    val status: String,
    val source: String,
    val result: MatchResultDto? = null,
)

@Serializable
data class MatchDetailDto(
    val id: Long,
    @SerialName("match_date") val matchDate: String,
    val league: LeagueDto,
    val season: SeasonDto,
    @SerialName("home_team") val homeTeam: TeamDto,
    @SerialName("away_team") val awayTeam: TeamDto,
    val status: String,
    val source: String,
    val result: MatchResultDto? = null,
    val odds: List<OddsDto> = emptyList(),
)

@Serializable
data class TeamDto(
    val id: Long,
    val name: String,
    val country: String,
)

@Serializable
data class LeagueDto(
    val id: Long,
    val name: String,
    val country: String,
)

@Serializable
data class SeasonDto(
    val id: Long,
    val name: String,
)

@Serializable
data class MatchResultDto(
    @SerialName("actual_outcome") val actualOutcome: Int,
    @SerialName("home_goals") val homeGoals: Int,
    @SerialName("away_goals") val awayGoals: Int,
    @SerialName("total_corners") val totalCorners: Int,
    @SerialName("total_yellow_cards") val totalYellowCards: Int,
)

@Serializable
data class OddsDto(
    val id: Long,
    val bookmaker: String,
    @SerialName("home_win_odds") val homeWinOdds: Double,
    @SerialName("draw_odds") val drawOdds: Double,
    @SerialName("away_win_odds") val awayWinOdds: Double,
    @SerialName("collected_at") val collectedAt: String,
)
