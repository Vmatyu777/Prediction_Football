package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.R
import com.predictionfootball.app.models.PredictionDto
import com.predictionfootball.app.ui.displayBinaryLabel
import com.predictionfootball.app.ui.displayOutcomeLong
import com.predictionfootball.app.ui.displayProbabilityLabel
import com.predictionfootball.app.ui.formatBackendUtcDateTime
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.KeyValueRow
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.PredictionViewModel
import com.predictionfootball.app.viewmodel.UiState

@Composable
fun PredictionRoute(
    viewModel: PredictionViewModel,
    onBack: () -> Unit,
) {
    val state by viewModel.state.collectAsState()

    PredictionScreen(
        state = state,
        onBack = onBack,
        onRetry = viewModel::generatePrediction,
    )
}

@Composable
fun PredictionScreen(
    state: UiState<PredictionDto>,
    onBack: () -> Unit,
    onRetry: () -> Unit,
) {
    ScreenScaffold(
        title = stringResource(R.string.prediction_result),
        subtitle = stringResource(R.string.prediction_result_subtitle),
        modifier = Modifier.verticalScroll(rememberScrollState()),
        actions = {
            OutlinedButton(onClick = onBack) {
                Text(stringResource(R.string.back))
            }
        },
    ) {
        when (state) {
            UiState.Loading -> LoadingContent(stringResource(R.string.generating_prediction))
            is UiState.Error -> ErrorContent(message = state.message, onRetry = onRetry)
            is UiState.Success -> PredictionContent(prediction = state.data)
        }
    }
}

@Composable
private fun PredictionContent(prediction: PredictionDto) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Text(
                text = stringResource(R.string.main_outcome),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(12.dp))
            KeyValueRow("Прогноз", displayOutcomeLong(prediction.outcome))
            ProbabilityRow(prediction.outcomeProbabilities)
        }

        PredictionMetricCards(prediction)

        InfoCard(modifier = Modifier.fillMaxWidth()) {
            KeyValueRow(stringResource(R.string.exact_score), prediction.exactScore)
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "${stringResource(R.string.created_at)}: ${formatBackendUtcDateTime(prediction.createdAt)}",
                modifier = Modifier.fillMaxWidth(),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.End,
            )
        }
    }
}

@Composable
private fun PredictionMetricCards(prediction: PredictionDto) {
    BoxWithConstraints {
        val useSingleColumn = maxWidth < 600.dp

        if (useSingleColumn) {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                PredictionMetricCard(
                    label = stringResource(R.string.btts),
                    value = displayBinaryLabel(prediction.btts),
                    probabilities = prediction.bttsProbabilities,
                    modifier = Modifier.fillMaxWidth(),
                )
                PredictionMetricCard(
                    label = stringResource(R.string.over25),
                    value = displayBinaryLabel(prediction.over25),
                    probabilities = prediction.over25Probabilities,
                    modifier = Modifier.fillMaxWidth(),
                )
                PredictionMetricCard(
                    label = stringResource(R.string.corners_over95),
                    value = displayBinaryLabel(prediction.cornersOver95),
                    probabilities = prediction.cornersOver95Probabilities,
                    modifier = Modifier.fillMaxWidth(),
                )
                PredictionMetricCard(
                    label = stringResource(R.string.yellow_cards_over35),
                    value = displayBinaryLabel(prediction.yellowCardsOver35),
                    probabilities = prediction.yellowCardsOver35Probabilities,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    PredictionMetricCard(
                        label = stringResource(R.string.btts),
                        value = displayBinaryLabel(prediction.btts),
                        probabilities = prediction.bttsProbabilities,
                        modifier = Modifier.weight(1f),
                    )
                    PredictionMetricCard(
                        label = stringResource(R.string.over25),
                        value = displayBinaryLabel(prediction.over25),
                        probabilities = prediction.over25Probabilities,
                        modifier = Modifier.weight(1f),
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    PredictionMetricCard(
                        label = stringResource(R.string.corners_over95),
                        value = displayBinaryLabel(prediction.cornersOver95),
                        probabilities = prediction.cornersOver95Probabilities,
                        modifier = Modifier.weight(1f),
                    )
                    PredictionMetricCard(
                        label = stringResource(R.string.yellow_cards_over35),
                        value = displayBinaryLabel(prediction.yellowCardsOver35),
                        probabilities = prediction.yellowCardsOver35Probabilities,
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}

@Composable
private fun PredictionMetricCard(
    label: String,
    value: String,
    probabilities: Map<String, Double>,
    modifier: Modifier = Modifier,
) {
    InfoCard(modifier = modifier) {
        KeyValueRow(label, value)
        ProbabilityRow(probabilities)
    }
}

@Composable
private fun ProbabilityRow(probabilities: Map<String, Double>) {
    Spacer(modifier = Modifier.height(8.dp))
    normalizedPercentages(probabilities).forEach { (label, percent) ->
        KeyValueRow(label = displayProbabilityLabel(label), value = "$percent%")
    }
}

internal fun normalizedPercentages(probabilities: Map<String, Double>): List<Pair<String, Int>> {
    if (probabilities.isEmpty()) {
        return emptyList()
    }

    val ordered = probabilities.entries.sortedBy { it.key }
    val rawPercentages = ordered.map { (_, value) -> value.coerceAtLeast(0.0) * 100.0 }
    val floored = rawPercentages.map { it.toInt() }.toMutableList()
    val difference = 100 - floored.sum()
    val fractionalOrder = rawPercentages
        .mapIndexed { index, value -> index to (value - value.toInt()) }
        .sortedWith(compareByDescending<Pair<Int, Double>> { it.second }.thenBy { it.first })

    if (difference > 0) {
        repeat(difference) { step ->
            val index = fractionalOrder[step % fractionalOrder.size].first
            floored[index] += 1
        }
    } else if (difference < 0) {
        val reverseFractionalOrder = fractionalOrder.asReversed()
        repeat(-difference) { step ->
            val index = reverseFractionalOrder[step % reverseFractionalOrder.size].first
            if (floored[index] > 0) {
                floored[index] -= 1
            }
        }
    }

    return ordered.mapIndexed { index, entry -> entry.key to floored[index] }
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun PredictionScreenPreview() {
    PredictionFootballTheme {
        PredictionScreen(
            state = UiState.Success(samplePrediction()),
            onBack = {},
            onRetry = {},
        )
    }
}

private fun samplePrediction() = PredictionDto(
    predictionId = 10,
    matchId = 1,
    createdAt = "2026-05-26 23:32:00.000000",
    outcome = "H",
    outcomeProbabilities = mapOf("H" to 0.52, "D" to 0.25, "A" to 0.23),
    btts = "Yes",
    bttsProbabilities = mapOf("No" to 0.42, "Yes" to 0.58),
    over25 = "Yes",
    over25Probabilities = mapOf("No" to 0.39, "Yes" to 0.61),
    cornersOver95 = "No",
    cornersOver95Probabilities = mapOf("No" to 0.55, "Yes" to 0.45),
    yellowCardsOver35 = "Yes",
    yellowCardsOver35Probabilities = mapOf("No" to 0.46, "Yes" to 0.54),
    exactScore = "2:1",
)
