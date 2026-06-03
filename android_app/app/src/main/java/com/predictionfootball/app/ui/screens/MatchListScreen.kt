package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
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
import com.predictionfootball.app.ui.displayMatchSource
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.components.SecondaryActionButton
import com.predictionfootball.app.ui.components.SectionTitle
import com.predictionfootball.app.ui.components.StatusBadge
import com.predictionfootball.app.ui.components.TeamMark
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.MatchListMode
import com.predictionfootball.app.viewmodel.MatchListViewModel
import com.predictionfootball.app.viewmodel.UiState
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

private val UpdatedTimeFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("HH:mm", Locale("ru"))

@Composable
fun MatchListRoute(
    viewModel: MatchListViewModel,
    onMatchClick: (Long) -> Unit,
    onProfileClick: () -> Unit,
) {
    val state by viewModel.state.collectAsState()
    val mode by viewModel.mode.collectAsState()
    val selectedLeague by viewModel.selectedLeague.collectAsState()
    val selectedSeason by viewModel.selectedSeason.collectAsState()
    val lastUpdatedAtMillis by viewModel.lastUpdatedAtMillis.collectAsState()

    LaunchedEffect(mode) {
        viewModel.refreshStaleCurrentMode()
    }

    MatchListScreen(
        state = state,
        selectedMode = mode,
        selectedLeague = selectedLeague,
        selectedSeason = selectedSeason,
        lastUpdatedAtMillis = lastUpdatedAtMillis,
        onModeChange = viewModel::loadMatches,
        onLeagueChange = viewModel::selectLeague,
        onSeasonChange = viewModel::selectSeason,
        onRetry = { viewModel.loadMatches() },
        onMatchClick = onMatchClick,
        onProfileClick = onProfileClick,
    )
}

@Composable
fun MatchListScreen(
    state: UiState<List<MatchSummaryDto>>,
    selectedMode: MatchListMode,
    selectedLeague: String?,
    selectedSeason: String?,
    lastUpdatedAtMillis: Long?,
    onModeChange: (MatchListMode) -> Unit,
    onLeagueChange: (String?) -> Unit,
    onSeasonChange: (String?) -> Unit,
    onRetry: () -> Unit,
    onMatchClick: (Long) -> Unit,
    onProfileClick: () -> Unit,
) {
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()

    LaunchedEffect(selectedMode, selectedLeague, selectedSeason) {
        listState.scrollToItem(0)
    }

    ScreenScaffold(
        title = stringResource(R.string.football_matches),
        subtitle = "Матчи, статусы и быстрый доступ к прогнозам",
        actions = {
            SecondaryActionButton(text = "Профиль", onClick = onProfileClick)
        },
    ) {
        SectionTitle(
            title = "Матч-центр",
            trailing = selectedMode.titleText(),
        )
        Spacer(modifier = Modifier.height(14.dp))
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            MatchListMode.entries.forEach { mode ->
                FilterChip(
                    selected = selectedMode == mode,
                    onClick = {
                        if (selectedMode == mode) {
                            onModeChange(mode)
                            coroutineScope.launch { listState.animateScrollToItem(0) }
                        } else {
                            onModeChange(mode)
                        }
                    },
                    label = { Text(mode.titleText()) },
                    shape = RoundedCornerShape(999.dp),
                    border = FilterChipDefaults.filterChipBorder(
                        enabled = true,
                        selected = selectedMode == mode,
                        borderColor = MaterialTheme.colorScheme.outline,
                        selectedBorderColor = MaterialTheme.colorScheme.primary,
                    ),
                    colors = FilterChipDefaults.filterChipColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                        labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        selectedContainerColor = MaterialTheme.colorScheme.primary,
                        selectedLabelColor = MaterialTheme.colorScheme.onPrimary,
                    ),
                )
            }
        }
        if (state is UiState.Success) {
            Spacer(modifier = Modifier.height(12.dp))
            BoxWithConstraints(modifier = Modifier.fillMaxWidth()) {
                val updatedText = lastUpdatedAtMillis?.let { "Обновлено: ${formatUpdatedTime(it)}" }
                if (maxWidth >= 640.dp) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.Bottom,
                    ) {
                        FilterRow(
                            matches = state.data,
                            selectedLeague = selectedLeague,
                            selectedSeason = selectedSeason,
                            onLeagueChange = onLeagueChange,
                            onSeasonChange = onSeasonChange,
                        )
                        updatedText?.let { text ->
                            Text(
                                text = text,
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                } else {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        FilterRow(
                            matches = state.data,
                            selectedLeague = selectedLeague,
                            selectedSeason = selectedSeason,
                            onLeagueChange = onLeagueChange,
                            onSeasonChange = onSeasonChange,
                        )
                        updatedText?.let { text ->
                            Text(
                                text = text,
                                modifier = Modifier.fillMaxWidth(),
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
        }
        Spacer(modifier = Modifier.height(16.dp))
        if (selectedMode == MatchListMode.Showcase) {
            InfoCard(modifier = Modifier.fillMaxWidth()) {
                Text(
                    text = "Примеры успешных прогнозов системы на исторических матчах.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Spacer(modifier = Modifier.height(16.dp))
        }

        when (state) {
            UiState.Loading -> LoadingContent(stringResource(R.string.loading_matches))
            is UiState.Error -> ErrorContent(message = state.message, onRetry = onRetry)
            is UiState.Success -> MatchList(
                matches = state.data.filterBy(selectedLeague, selectedSeason),
                selectedMode = selectedMode,
                listState = listState,
                onMatchClick = onMatchClick,
            )
        }
    }
}

@Composable
private fun FilterRow(
    matches: List<MatchSummaryDto>,
    selectedLeague: String?,
    selectedSeason: String?,
    onLeagueChange: (String?) -> Unit,
    onSeasonChange: (String?) -> Unit,
) {
    Row(
        modifier = Modifier.horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        FilterMenu(
            label = "Лига",
            selectedValue = selectedLeague,
            options = matches.map { it.league }.distinct().sorted(),
            onValueChange = onLeagueChange,
        )
        FilterMenu(
            label = "Сезон",
            selectedValue = selectedSeason,
            options = matches.map { it.season }.distinct().sortedDescending(),
            onValueChange = onSeasonChange,
        )
    }
}

@Composable
private fun FilterMenu(
    label: String,
    selectedValue: String?,
    options: List<String>,
    onValueChange: (String?) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val dropdownScrollState = rememberScrollState()

    LaunchedEffect(expanded) {
        if (expanded) {
            dropdownScrollState.scrollTo(0)
        }
    }

    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Box {
            androidx.compose.material3.OutlinedButton(
                onClick = { expanded = true },
                modifier = Modifier
                    .height(44.dp)
                    .width(172.dp),
                shape = RoundedCornerShape(14.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.onSurface,
                ),
            ) {
                Text(
                    text = selectedValue ?: "Все",
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            DropdownMenu(
                expanded = expanded,
                onDismissRequest = { expanded = false },
                modifier = Modifier
                    .width(172.dp)
                    .heightIn(max = 300.dp),
                containerColor = MaterialTheme.colorScheme.surface,
                tonalElevation = 0.dp,
            ) {
                Column(
                    modifier = Modifier
                        .heightIn(max = 300.dp)
                        .verticalScroll(dropdownScrollState),
                ) {
                    DropdownMenuItem(
                        text = { Text("Все") },
                        onClick = {
                            onValueChange(null)
                            expanded = false
                        },
                    )
                    options.forEach { option ->
                        DropdownMenuItem(
                            text = {
                                Text(
                                    text = option,
                                    maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        },
                        onClick = {
                            onValueChange(option)
                                expanded = false
                            },
                        )
                    }
                }
            }
        }
    }
}

private fun List<MatchSummaryDto>.filterBy(league: String?, season: String?): List<MatchSummaryDto> {
    return filter { match ->
        (league == null || match.league == league) &&
            (season == null || match.season == season)
    }
}

@Composable
private fun MatchList(
    matches: List<MatchSummaryDto>,
    selectedMode: MatchListMode,
    listState: LazyListState,
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
        state = listState,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        val demoMatches = matches.filter { it.source.equals("demo", ignoreCase = true) }
        val regularMatches = matches.filterNot { it.source.equals("demo", ignoreCase = true) }

        if (regularMatches.isNotEmpty()) {
            if (selectedMode == MatchListMode.Upcoming) {
                item(key = "regular-header") {
                    Text(
                        text = "Актуальные матчи",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
            items(regularMatches, key = { it.id }) { match ->
                MatchCard(match = match, onClick = { onMatchClick(match.id) })
            }
        }

        if (demoMatches.isNotEmpty()) {
            if (selectedMode == MatchListMode.Upcoming && regularMatches.isEmpty()) {
                item(key = "demo-explanation") {
                    InfoCard(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            text = "Актуальных матчей пока нет. Ниже показаны демонстрационные матчи для проверки работы прогноза.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
            item(key = "demo-header") {
                Text(
                    text = "Демонстрационные матчи",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                )
            }
            items(demoMatches, key = { it.id }) { match ->
                MatchCard(match = match, onClick = { onMatchClick(match.id) }, isDemo = true)
            }
        }
    }
}

@Composable
private fun MatchCard(match: MatchSummaryDto, onClick: () -> Unit, isDemo: Boolean = false) {
    InfoCard(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "${match.league} · ${match.season}",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (isDemo) {
                    StatusBadge(text = "Демо", accent = MaterialTheme.colorScheme.secondary)
                }
                StatusBadge(text = displayMatchStatus(match.status))
            }
        }
        Spacer(modifier = Modifier.height(18.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            TeamBlock(name = match.homeTeam, modifier = Modifier.weight(1f))
            ScoreBlock(match = match, modifier = Modifier.widthIn(min = 92.dp))
            TeamBlock(name = match.awayTeam, modifier = Modifier.weight(1f), alignEnd = true)
        }
        Spacer(modifier = Modifier.height(16.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            Text(
                text = formatDate(match.matchDate),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            val sourceLabel = displayMatchSource(match.source)
            if (sourceLabel.isNotBlank() && !isDemo) {
                StatusBadge(
                    text = sourceLabel,
                    accent = MaterialTheme.colorScheme.secondary,
                )
            }
        }
    }
}

@Composable
private fun TeamBlock(name: String, modifier: Modifier = Modifier, alignEnd: Boolean = false) {
    Column(
        modifier = modifier,
        horizontalAlignment = if (alignEnd) {
            androidx.compose.ui.Alignment.End
        } else {
            androidx.compose.ui.Alignment.Start
        },
    ) {
        TeamMark(name = name)
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = name,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun ScoreBlock(match: MatchSummaryDto, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier,
        contentAlignment = androidx.compose.ui.Alignment.Center,
    ) {
        Column(horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
            Text(
                text = if (match.result != null) {
                    "${match.result.homeGoals} : ${match.result.awayGoals}"
                } else {
                    "—"
                },
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Black,
            )
            Text(
                text = if (match.result != null) stringResource(R.string.final_score) else "VS",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
            )
        }
    }
}

internal fun formatDate(value: String): String = value
    .replace("T", " ")
    .substringBefore(".")

private fun formatUpdatedTime(value: Long): String {
    return Instant.ofEpochMilli(value)
        .atZone(ZoneId.systemDefault())
        .format(UpdatedTimeFormatter)
}

@Composable
private fun MatchListMode.titleText(): String = when (this) {
    MatchListMode.Recent -> stringResource(R.string.recent_matches)
    MatchListMode.Upcoming -> stringResource(R.string.upcoming_matches)
    MatchListMode.Showcase -> stringResource(R.string.showcase_matches)
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun MatchListScreenPreview() {
    PredictionFootballTheme {
        MatchListScreen(
            state = UiState.Success(sampleMatches()),
            selectedMode = MatchListMode.Recent,
            selectedLeague = null,
            selectedSeason = null,
            lastUpdatedAtMillis = System.currentTimeMillis(),
            onModeChange = {},
            onLeagueChange = {},
            onSeasonChange = {},
            onRetry = {},
            onMatchClick = {},
            onProfileClick = {},
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
        source = "historical",
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
        source = "demo",
        result = null,
    ),
)
