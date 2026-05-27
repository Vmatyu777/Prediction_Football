package com.predictionfootball.app.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PredictionDto(
    @SerialName("prediction_id") val predictionId: Long,
    @SerialName("match_id") val matchId: Long,
    @SerialName("created_at") val createdAt: String,
    val outcome: String,
    @SerialName("outcome_probabilities") val outcomeProbabilities: Map<String, Double>,
    val btts: String,
    @SerialName("btts_probabilities") val bttsProbabilities: Map<String, Double>,
    val over25: String,
    @SerialName("over25_probabilities") val over25Probabilities: Map<String, Double>,
    @SerialName("corners_over95") val cornersOver95: String,
    @SerialName("corners_over95_probabilities") val cornersOver95Probabilities: Map<String, Double>,
    @SerialName("yellow_cards_over35") val yellowCardsOver35: String,
    @SerialName("yellow_cards_over35_probabilities") val yellowCardsOver35Probabilities: Map<String, Double>,
    @SerialName("exact_score") val exactScore: String,
    @SerialName("feature_debug") val featureDebug: Map<String, FeatureDebugDto> = emptyMap(),
)

@Serializable
data class FeatureDebugDto(
    @SerialName("feature_count") val featureCount: Int? = null,
    @SerialName("expected_feature_count") val expectedFeatureCount: Int? = null,
    @SerialName("missing_count") val missingCount: Int? = null,
    @SerialName("nan_count") val nanCount: Int? = null,
    @SerialName("order_matches") val orderMatches: Boolean? = null,
    @SerialName("missing_features") val missingFeatures: List<String> = emptyList(),
)
