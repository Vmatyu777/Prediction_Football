package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.models.MatchResultDto
import com.predictionfootball.app.models.PredictionHistoryDto
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.KeyValueRow
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.ScreenScaffold
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
    ScreenScaffold(
        title = "История прогнозов",
        subtitle = "Последние запросы по матчам",
        actions = {
            OutlinedButton(onClick = onBack) {
                Text("Назад")
            }
        },
    ) {
        when {
            state.isLoading && state.history.isEmpty() -> LoadingContent("Загрузка истории")
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

    if (latestUniqueHistory.isEmpty()) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Text("История пока пуста", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        return
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        items(latestUniqueHistory, key = { it.predictionId }) { historyItem ->
            HistoryCard(historyItem)
        }
    }
}

@Composable
private fun HistoryCard(item: PredictionHistoryDto) {
    InfoCard(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = "${item.homeTeam} - ${item.awayTeam}",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
        )
        Spacer(modifier = Modifier.height(12.dp))
        KeyValueRow("Лига", item.league)
        Spacer(modifier = Modifier.height(8.dp))
        KeyValueRow("Сезон", item.season)
        Spacer(modifier = Modifier.height(8.dp))
        KeyValueRow("Дата запроса", formatBackendUtcDateTime(item.queryDate))
        Spacer(modifier = Modifier.height(8.dp))
        ForecastComparisonRow(
            label = "Исход матча",
            prediction = displayOutcomeLong(item.outcome),
            fact = item.result?.let { displayOutcomeLong(actualOutcomeCode(it.actualOutcome)) },
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
        Spacer(modifier = Modifier.height(8.dp))
        KeyValueRow("Статус", predictionSummary(item))
    }
}

@Composable
private fun ForecastComparisonRow(
    label: String,
    prediction: String,
    fact: String?,
) {
    val value = if (fact == null) {
        "Прогноз: $prediction; Факт: Матч не завершен"
    } else {
        val status = if (prediction == fact) "Угадано" else "Не угадано"
        "Прогноз: $prediction; Факт: $fact; $status"
    }
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.SemiBold,
        )
    }
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
    val result = item.result ?: return "Матч не завершен"
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
        return "Факт недоступен"
    }
    return "Угадано: ${checks.count { it }} из ${checks.size} показателей"
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
