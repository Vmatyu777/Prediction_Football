package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.R
import com.predictionfootball.app.models.LeagueDto
import com.predictionfootball.app.models.MatchDetailDto
import com.predictionfootball.app.models.OddsDto
import com.predictionfootball.app.models.SeasonDto
import com.predictionfootball.app.models.TeamDto
import com.predictionfootball.app.ui.displayBookmaker
import com.predictionfootball.app.ui.displayMatchStatus
import com.predictionfootball.app.ui.displayMatchSource
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.KeyValueRow
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.PrimaryActionButton
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.MatchDetailsViewModel
import com.predictionfootball.app.viewmodel.UiState

@Composable
fun MatchDetailsRoute(
    viewModel: MatchDetailsViewModel,
    onBack: () -> Unit,
    onGeneratePrediction: (Long) -> Unit,
) {
    val state by viewModel.state.collectAsState()

    MatchDetailsScreen(
        state = state,
        onBack = onBack,
        onRetry = viewModel::loadMatch,
        onGeneratePrediction = onGeneratePrediction,
    )
}

@Composable
fun MatchDetailsScreen(
    state: UiState<MatchDetailDto>,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onGeneratePrediction: (Long) -> Unit,
) {
    ScreenScaffold(
        title = stringResource(R.string.match_details),
        subtitle = stringResource(R.string.match_details_subtitle),
        modifier = Modifier.verticalScroll(rememberScrollState()),
        actions = {
            OutlinedButton(onClick = onBack) {
                Text(stringResource(R.string.back))
            }
        },
    ) {
        when (state) {
            UiState.Loading -> LoadingContent(stringResource(R.string.loading_match_details))
            is UiState.Error -> ErrorContent(message = state.message, onRetry = onRetry)
            is UiState.Success -> MatchDetailsContent(
                match = state.data,
                onGeneratePrediction = onGeneratePrediction,
            )
        }
    }
}

@Composable
private fun MatchDetailsContent(
    match: MatchDetailDto,
    onGeneratePrediction: (Long) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Text(
                text = "${match.homeTeam.name} vs ${match.awayTeam.name}",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(12.dp))
            KeyValueRow(stringResource(R.string.date), formatDate(match.matchDate))
            KeyValueRow(stringResource(R.string.league), "${match.league.name}, ${match.league.country}")
            KeyValueRow(stringResource(R.string.season), match.season.name)
            KeyValueRow(stringResource(R.string.status), displayMatchStatus(match.status))
            val sourceLabel = displayMatchSource(match.source)
            if (sourceLabel.isNotBlank()) {
                KeyValueRow("Источник", sourceLabel)
            }
            if (match.result != null) {
                KeyValueRow(stringResource(R.string.final_score), "${match.result.homeGoals}:${match.result.awayGoals}")
                KeyValueRow(stringResource(R.string.corners), match.result.totalCorners.toString())
                KeyValueRow(stringResource(R.string.yellow_cards), match.result.totalYellowCards.toString())
            }
        }

        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Text(
                text = stringResource(R.string.latest_odds),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(12.dp))
            val latestOdds = match.odds.maxByOrNull { it.collectedAt }
            if (latestOdds == null) {
                Text(stringResource(R.string.no_odds_available), color = MaterialTheme.colorScheme.onSurfaceVariant)
            } else {
                Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                    OddsValue(stringResource(R.string.home), latestOdds.homeWinOdds)
                    OddsValue(stringResource(R.string.draw), latestOdds.drawOdds)
                    OddsValue(stringResource(R.string.away), latestOdds.awayWinOdds)
                }
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = displayBookmaker(latestOdds.bookmaker),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        PrimaryActionButton(
            text = stringResource(R.string.generate_prediction),
            onClick = { onGeneratePrediction(match.id) },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}

@Composable
private fun OddsValue(label: String, value: Double) {
    Column {
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text("%.2f".format(value), fontWeight = FontWeight.Bold)
    }
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun MatchDetailsScreenPreview() {
    PredictionFootballTheme {
        MatchDetailsScreen(
            state = UiState.Success(sampleMatchDetails()),
            onBack = {},
            onRetry = {},
            onGeneratePrediction = {},
        )
    }
}

internal fun sampleMatchDetails() = MatchDetailDto(
    id = 1,
    matchDate = "2025-05-18T17:30:00",
    league = LeagueDto(1, "E0", "England"),
    season = SeasonDto(1, "2024/25"),
    homeTeam = TeamDto(1, "Arsenal", "England"),
    awayTeam = TeamDto(2, "Chelsea", "England"),
    status = "Finished",
    source = "historical",
    result = sampleMatches().first().result,
    odds = listOf(
        OddsDto(
            id = 1,
            bookmaker = "Average Market Odds",
            homeWinOdds = 1.95,
            drawOdds = 3.45,
            awayWinOdds = 4.10,
            collectedAt = "2025-05-18T12:00:00",
        ),
    ),
)
