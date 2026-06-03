package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.models.MatchResultDto
import com.predictionfootball.app.models.PredictionHistoryDto
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.components.SecondaryActionButton
import com.predictionfootball.app.ui.components.SectionTitle
import com.predictionfootball.app.ui.components.StatusBadge
import com.predictionfootball.app.ui.displayBinaryLabel
import com.predictionfootball.app.ui.displayOutcomeLong
import com.predictionfootball.app.ui.formatBackendUtcDateTime
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.AuthViewModel
import com.predictionfootball.app.viewmodel.ProfileState

@Composable
fun HistoryRoute(
    viewModel: AuthViewModel,
    onBack: () -> Unit,
    onSessionExpired: () -> Unit,
) {
    val state by viewModel.profileState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadHistory(onSessionExpired)
    }

    HistoryScreen(
        state = state,
        onBack = onBack,
        onRetry = { viewModel.loadHistory(onSessionExpired) },
    )
}

@Composable
fun HistoryScreen(
    state: ProfileState,
    onBack: () -> Unit,
    onRetry: () -> Unit,
) {
    val isInitialHistoryLoading = state.historyLoading &&
        state.history.isEmpty() &&
        state.errorMessage == null
    val isInitialHistoryPending = !state.hasLoadedHistory &&
        state.history.isEmpty() &&
        state.errorMessage == null

    ScreenScaffold(
        title = "История прогнозов",
        subtitle = "Последние сохранённые аналитические запросы",
        actions = {
            SecondaryActionButton(text = "Назад", onClick = onBack)
        },
    ) {
        when {
            isInitialHistoryLoading -> LoadingContent("Загрузка истории")
            isInitialHistoryPending -> Unit
            state.errorMessage != null && state.history.isEmpty() -> ErrorContent(
                message = state.errorMessage,
                onRetry = onRetry,
            )
            else -> HistoryList(history = state.history)
        }
    }
}

@Composable
private fun HistoryList(history: List<PredictionHistoryDto>) {
    val latestUniqueHistory = history
        .sortedByDescending { it.queryDate }
        .distinctBy { it.predictionId }
    val listState = rememberLazyListState()

    LaunchedEffect(latestUniqueHistory.size, latestUniqueHistory.firstOrNull()?.predictionId) {
        if (latestUniqueHistory.isNotEmpty()) {
            listState.scrollToItem(0)
        }
    }

    if (latestUniqueHistory.isEmpty()) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Text("История пока пуста", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        return
    }

    LazyColumn(
        state = listState,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(latestUniqueHistory, key = { it.predictionId }) { historyItem ->
            HistoryCard(historyItem)
        }
    }
}

@Composable
private fun HistoryCard(item: PredictionHistoryDto) {
    InfoCard(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "${item.homeTeam} - ${item.awayTeam}",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    text = "${item.league} · ${item.season}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            StatusBadge(if (item.result == null) "Ожидается" else "Верно: ${predictionSummary(item)}")
        }
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            text = "Запрос: ${formatBackendUtcDateTime(item.queryDate)}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(modifier = Modifier.height(14.dp))
        SectionTitle("Рынки прогноза")
        Spacer(modifier = Modifier.height(10.dp))
        ForecastComparisonRow(
            label = "Исход матча",
            prediction = displayOutcomeLong(item.outcome),
            fact = item.result?.let { displayOutcomeLong(actualOutcomeCode(it.actualOutcome)) },
            isPrimary = true,
        )
        item.btts?.let { value ->
            Spacer(modifier = Modifier.height(8.dp))
            ForecastComparisonRow(
                label = "Обе забьют",
                prediction = displayBinaryLabel(value),
                fact = item.result?.let { displayBinaryLabel(binaryFact(it.homeGoals > 0 && it.awayGoals > 0)) },
            )
        }
        item.over25?.let { value ->
            Spacer(modifier = Modifier.height(8.dp))
            ForecastComparisonRow(
                label = "Голы: тотал > 2.5",
                prediction = displayBinaryLabel(value),
                fact = item.result?.let { displayBinaryLabel(binaryFact((it.homeGoals + it.awayGoals) > 2.5)) },
            )
        }
        item.cornersOver95?.let { value ->
            Spacer(modifier = Modifier.height(8.dp))
            ForecastComparisonRow(
                label = "Угловые: тотал > 9.5",
                prediction = displayBinaryLabel(value),
                fact = item.result?.let { displayBinaryLabel(binaryFact(it.totalCorners > 9.5)) },
            )
        }
        item.yellowCardsOver35?.let { value ->
            Spacer(modifier = Modifier.height(8.dp))
            ForecastComparisonRow(
                label = "ЖК: тотал > 3.5",
                prediction = displayBinaryLabel(value),
                fact = item.result?.let { displayBinaryLabel(binaryFact(it.totalYellowCards > 3.5)) },
            )
        }
        if (!item.exactScore.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(8.dp))
            ForecastComparisonRow(
                label = "Точный счет",
                prediction = item.exactScore,
                fact = item.result?.let { actualScore(it.homeGoals, it.awayGoals) },
            )
        }
    }
}

@Composable
private fun ForecastComparisonRow(
    label: String,
    prediction: String,
    fact: String?,
    isPrimary: Boolean = false,
) {
    val isHit = fact != null && prediction == fact
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        color = if (isPrimary) {
            MaterialTheme.colorScheme.primary.copy(alpha = 0.08f)
        } else {
            MaterialTheme.colorScheme.surfaceVariant
        },
        border = BorderStroke(
            1.dp,
            if (isPrimary) MaterialTheme.colorScheme.primary.copy(alpha = 0.4f) else MaterialTheme.colorScheme.outline,
        ),
    ) {
        BoxWithConstraints {
            val compact = maxWidth < 560.dp
            if (compact) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    MarketLabel(label)
                    MarketValue(label = "Прогноз", value = prediction)
                    MarketValue(label = "Факт", value = fact ?: "Ожидается")
                    HistoryStatusBadge(fact = fact, isHit = isHit)
                }
            } else {
                val rowHeight = if (isPrimary) 104.dp else 78.dp
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(rowHeight)
                        .padding(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.spacedBy(14.dp),
                    verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1.25f)) {
                        MarketLabel(label)
                    }
                    MarketValue(label = "Прогноз", value = prediction, modifier = Modifier.weight(1.1f))
                    MarketValue(label = "Факт", value = fact ?: "Ожидается", modifier = Modifier.weight(1.1f))
                    HistoryStatusBadge(fact = fact, isHit = isHit)
                }
            }
        }
    }
}

@Composable
private fun HistoryStatusBadge(fact: String?, isHit: Boolean) {
    StatusBadge(
        text = if (fact == null) "Ожидается" else if (isHit) "Верно" else "Ошибка",
        modifier = Modifier.width(112.dp),
        accent = historyStatusColor(fact = fact, isHit = isHit),
    )
}

@Composable
private fun MarketLabel(label: String) {
    Text(
        text = label,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        fontWeight = FontWeight.SemiBold,
        maxLines = 2,
        overflow = TextOverflow.Ellipsis,
    )
}

@Composable
private fun MarketValue(label: String, value: String, modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Bold,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun historyStatusColor(fact: String?, isHit: Boolean) = if (fact == null) {
    MaterialTheme.colorScheme.onSurfaceVariant
} else if (isHit) {
    MaterialTheme.colorScheme.primary
} else {
    MaterialTheme.colorScheme.error
}

private fun actualOutcomeCode(value: Int): String = when (value) {
    0 -> "A"
    1 -> "D"
    2 -> "H"
    else -> value.toString()
}

private fun binaryFact(value: Boolean): String = if (value) "Yes" else "No"

private fun actualScore(homeGoals: Int, awayGoals: Int): String = "$homeGoals:$awayGoals"

private fun predictionSummary(item: PredictionHistoryDto): String {
    val result = item.result ?: return "Ожидается"
    val checks = buildList {
        add(actualOutcomeCode(result.actualOutcome) == item.outcome)
        item.btts?.let { add(it == binaryFact(result.homeGoals > 0 && result.awayGoals > 0)) }
        item.over25?.let { add(it == binaryFact((result.homeGoals + result.awayGoals) > 2.5)) }
        item.cornersOver95?.let { add(it == binaryFact(result.totalCorners > 9.5)) }
        item.yellowCardsOver35?.let { add(it == binaryFact(result.totalYellowCards > 3.5)) }
        item.exactScore?.takeIf { it.isNotBlank() }?.let {
            add(it == actualScore(result.homeGoals, result.awayGoals))
        }
    }
    if (checks.isEmpty()) {
        return "0/0"
    }
    return "${checks.count { it }}/${checks.size}"
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun HistoryScreenPreview() {
    PredictionFootballTheme {
        HistoryScreen(
            state = ProfileState(
                history = listOf(
                    PredictionHistoryDto(
                        id = 1,
                        queryDate = "2026-05-27T16:58:00.123456",
                        predictionId = 10,
                        matchId = 100,
                        matchDate = "2025-05-18T17:30:00",
                        league = "E0",
                        season = "2024/25",
                        homeTeam = "Arsenal",
                        awayTeam = "Chelsea",
                        predictionCreatedAt = "2026-05-27T16:57:00.123456",
                        outcome = "H",
                        btts = "Yes",
                        over25 = "No",
                        cornersOver95 = "Yes",
                        yellowCardsOver35 = "No",
                        exactScore = "2:1",
                        result = MatchResultDto(
                            actualOutcome = 2,
                            homeGoals = 2,
                            awayGoals = 1,
                            totalCorners = 10,
                            totalYellowCards = 3,
                        ),
                    ),
                ),
            ),
            onBack = {},
            onRetry = {},
        )
    }
}
