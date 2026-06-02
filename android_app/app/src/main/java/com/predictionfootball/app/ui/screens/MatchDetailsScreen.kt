package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
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
import com.predictionfootball.app.ui.components.SecondaryActionButton
import com.predictionfootball.app.ui.components.SectionTitle
import com.predictionfootball.app.ui.components.StatusBadge
import com.predictionfootball.app.ui.components.TeamMark
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
    val detailsScrollState = rememberScrollState()

    ScreenScaffold(
        title = stringResource(R.string.match_details),
        subtitle = "Форма матча, результат и рыночные коэффициенты",
        actions = {
            SecondaryActionButton(text = stringResource(R.string.back), onClick = onBack)
        },
    ) {
        when (state) {
            UiState.Loading -> LoadingContent(stringResource(R.string.loading_match_details))
            is UiState.Error -> ErrorContent(message = state.message, onRetry = onRetry)
            is UiState.Success -> MatchDetailsContent(
                match = state.data,
                onGeneratePrediction = onGeneratePrediction,
                modifier = Modifier.verticalScroll(detailsScrollState),
            )
        }
    }
}

@Composable
private fun MatchDetailsContent(
    match: MatchDetailDto,
    onGeneratePrediction: (Long) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        MatchHeaderCard(match)
        BoxWithConstraints {
            if (maxWidth >= 760.dp) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    MatchFactsCard(match, modifier = Modifier.weight(0.42f))
                    OddsCard(match, modifier = Modifier.weight(0.58f))
                }
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    MatchFactsCard(match)
                    OddsCard(match)
                }
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
private fun OddsCard(match: MatchDetailDto, modifier: Modifier = Modifier) {
    InfoCard(modifier = modifier.fillMaxWidth()) {
        SectionTitle(stringResource(R.string.latest_odds))
        Spacer(modifier = Modifier.height(10.dp))
        val latestOdds = match.odds.maxByOrNull { it.collectedAt }
        if (latestOdds == null) {
            Text(stringResource(R.string.no_odds_available), color = MaterialTheme.colorScheme.onSurfaceVariant)
        } else {
            BoxWithConstraints {
                val singleColumn = maxWidth < 520.dp
                if (singleColumn) {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        OddsValue(stringResource(R.string.home), latestOdds.homeWinOdds, Modifier.fillMaxWidth())
                        OddsValue(stringResource(R.string.draw), latestOdds.drawOdds, Modifier.fillMaxWidth())
                        OddsValue(stringResource(R.string.away), latestOdds.awayWinOdds, Modifier.fillMaxWidth())
                    }
                } else {
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        OddsValue(stringResource(R.string.home), latestOdds.homeWinOdds, Modifier.weight(1f))
                        OddsValue(stringResource(R.string.draw), latestOdds.drawOdds, Modifier.weight(1f))
                        OddsValue(stringResource(R.string.away), latestOdds.awayWinOdds, Modifier.weight(1f))
                    }
                }
            }
            Spacer(modifier = Modifier.height(10.dp))
            Text(
                text = displayBookmaker(latestOdds.bookmaker),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun MatchHeaderCard(match: MatchDetailDto) {
    InfoCard(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            StatusBadge(text = displayMatchStatus(match.status))
            Text(
                text = formatDate(match.matchDate),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Spacer(modifier = Modifier.height(12.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            MatchTeamColumn(match.homeTeam.name, Modifier.weight(1f))
            Column(horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
                Text(
                    text = match.result?.let { "${it.homeGoals} : ${it.awayGoals}" } ?: "—",
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.onSurface,
                    fontWeight = FontWeight.Black,
                )
                Text(
                    text = "${match.league.name} · ${match.season.name}",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                )
            }
            MatchTeamColumn(match.awayTeam.name, Modifier.weight(1f), alignEnd = true)
        }
    }
}

@Composable
private fun MatchTeamColumn(name: String, modifier: Modifier = Modifier, alignEnd: Boolean = false) {
    Column(
        modifier = modifier,
        horizontalAlignment = if (alignEnd) androidx.compose.ui.Alignment.End else androidx.compose.ui.Alignment.Start,
    ) {
        TeamMark(name)
        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = name,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Bold,
            maxLines = 2,
        )
    }
}

@Composable
private fun MatchFactsCard(match: MatchDetailDto, modifier: Modifier = Modifier) {
    InfoCard(modifier = modifier.fillMaxWidth()) {
        SectionTitle("Информация о матче")
        Spacer(modifier = Modifier.height(10.dp))
        KeyValueRow(stringResource(R.string.league), "${match.league.name}, ${match.league.country}")
        Spacer(modifier = Modifier.height(8.dp))
        KeyValueRow(stringResource(R.string.season), match.season.name)
        val sourceLabel = displayMatchSource(match.source)
        if (sourceLabel.isNotBlank()) {
            Spacer(modifier = Modifier.height(8.dp))
            KeyValueRow("Источник", sourceLabel)
        }
        if (match.result != null) {
            Spacer(modifier = Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                ResultStat("Счет", "${match.result.homeGoals}:${match.result.awayGoals}", Modifier.weight(1f))
                ResultStat(stringResource(R.string.corners), match.result.totalCorners.toString(), Modifier.weight(1f))
                ResultStat(stringResource(R.string.yellow_cards), match.result.totalYellowCards.toString(), Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun ResultStat(label: String, value: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
    ) {
        Column(modifier = Modifier.fillMaxWidth().height(68.dp), verticalArrangement = Arrangement.Center) {
            Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
                Text(
                    text = value,
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Black,
                )
                Text(
                    text = label,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                )
            }
        }
    }
}

@Composable
private fun OddsValue(label: String, value: Double, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
    ) {
        Column(modifier = Modifier.fillMaxWidth().height(72.dp), verticalArrangement = Arrangement.Center) {
            Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
                Text(
                    label,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "%.2f".format(value),
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Black,
                )
            }
        }
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
