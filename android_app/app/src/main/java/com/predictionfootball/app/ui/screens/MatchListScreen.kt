package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.R
import com.predictionfootball.app.models.MatchResultDto
import com.predictionfootball.app.models.MatchSummaryDto
import com.predictionfootball.app.ui.displayMatchStatus
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.KeyValueRow
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.MatchListMode
import com.predictionfootball.app.viewmodel.MatchListViewModel
import com.predictionfootball.app.viewmodel.UiState

@Composable
fun MatchListRoute(
    viewModel: MatchListViewModel,
    onMatchClick: (Long) -> Unit,
) {
    val state by viewModel.state.collectAsState()
    val mode by viewModel.mode.collectAsState()

    MatchListScreen(
        state = state,
        selectedMode = mode,
        onModeChange = viewModel::loadMatches,
        onRetry = { viewModel.loadMatches() },
        onMatchClick = onMatchClick,
    )
}

@Composable
fun MatchListScreen(
    state: UiState<List<MatchSummaryDto>>,
    selectedMode: MatchListMode,
    onModeChange: (MatchListMode) -> Unit,
    onRetry: () -> Unit,
    onMatchClick: (Long) -> Unit,
) {
    ScreenScaffold(
        title = stringResource(R.string.football_matches),
        subtitle = stringResource(R.string.match_list_subtitle),
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MatchListMode.entries.forEach { mode ->
                FilterChip(
                    selected = selectedMode == mode,
                    onClick = { onModeChange(mode) },
                    label = { Text(mode.titleText()) },
                )
            }
        }
        Spacer(modifier = Modifier.height(16.dp))

        when (state) {
            UiState.Loading -> LoadingContent(stringResource(R.string.loading_matches))
            is UiState.Error -> ErrorContent(message = state.message, onRetry = onRetry)
            is UiState.Success -> MatchList(
                matches = state.data,
                selectedMode = selectedMode,
                onMatchClick = onMatchClick,
            )
        }
    }
}

@Composable
private fun MatchList(
    matches: List<MatchSummaryDto>,
    selectedMode: MatchListMode,
    onMatchClick: (Long) -> Unit,
) {
    if (matches.isEmpty()) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Text(
                if (selectedMode == MatchListMode.Upcoming) {
                    stringResource(R.string.no_upcoming_matches)
                } else {
                    stringResource(R.string.no_matches)
                }
            )
        }
        return
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(matches, key = { it.id }) { match ->
            MatchCard(match = match, onClick = { onMatchClick(match.id) })
        }
    }
}

@Composable
private fun MatchCard(match: MatchSummaryDto, onClick: () -> Unit) {
    InfoCard(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "${match.homeTeam} vs ${match.awayTeam}",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "${formatDate(match.matchDate)} | ${match.league} | ${match.season}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                text = displayMatchStatus(match.status),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
        }
        if (match.result != null) {
            Spacer(modifier = Modifier.height(12.dp))
            KeyValueRow(
                label = stringResource(R.string.final_score),
                value = "${match.result.homeGoals}:${match.result.awayGoals}",
            )
        }
    }
}

internal fun formatDate(value: String): String = value
    .replace("T", " ")
    .substringBefore(".")

@Composable
private fun MatchListMode.titleText(): String = when (this) {
    MatchListMode.Recent -> stringResource(R.string.recent_matches)
    MatchListMode.Upcoming -> stringResource(R.string.upcoming_matches)
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun MatchListScreenPreview() {
    PredictionFootballTheme {
        MatchListScreen(
            state = UiState.Success(sampleMatches()),
            selectedMode = MatchListMode.Recent,
            onModeChange = {},
            onRetry = {},
            onMatchClick = {},
        )
    }
}

internal fun sampleMatches() = listOf(
    MatchSummaryDto(
        id = 1,
        matchDate = "2025-05-18T17:30:00",
        league = "E0",
        season = "2024/25",
        homeTeam = "Arsenal",
        awayTeam = "Chelsea",
        status = "Finished",
        result = MatchResultDto(2, 2, 1, 9, 4),
    ),
    MatchSummaryDto(
        id = 2,
        matchDate = "2025-05-19T20:00:00",
        league = "SP1",
        season = "2024/25",
        homeTeam = "Barcelona",
        awayTeam = "Real Madrid",
        status = "Scheduled",
        result = null,
    ),
)
