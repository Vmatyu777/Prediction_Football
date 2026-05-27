package com.predictionfootball.app.viewmodel

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.predictionfootball.app.models.PredictionDto
import com.predictionfootball.app.network.PredictionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class PredictionViewModel(
    savedStateHandle: SavedStateHandle,
) : ViewModel() {
    private val repository = PredictionRepository()
    private val matchId: Long = checkNotNull(savedStateHandle["matchId"])

    private val _state = MutableStateFlow<UiState<PredictionDto>>(UiState.Loading)
    val state: StateFlow<UiState<PredictionDto>> = _state.asStateFlow()

    init {
        generatePrediction()
    }

    fun generatePrediction() {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                repository.generatePrediction(matchId)
            }.onSuccess { prediction ->
                _state.value = UiState.Success(prediction)
            }.onFailure { error ->
                _state.value = UiState.Error(error.message ?: "Unable to generate prediction")
            }
        }
    }
}
