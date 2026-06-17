package com.predictionfootball.app.viewmodel

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.predictionfootball.app.models.MatchDetailDto
import com.predictionfootball.app.models.MatchTeamFormDto
import com.predictionfootball.app.network.PredictionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MatchDetailsViewModel(
    savedStateHandle: SavedStateHandle,
) : ViewModel() {
    private val repository = PredictionRepository()
    private val matchId: Long = checkNotNull(savedStateHandle["matchId"])

    private val _state = MutableStateFlow<UiState<MatchDetailsUiData>>(UiState.Loading)
    val state: StateFlow<UiState<MatchDetailsUiData>> = _state.asStateFlow()

    init {
        loadMatch()
    }

    fun loadMatch() {
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                val match = repository.matchDetails(matchId)
                val teamForm = runCatching { repository.matchTeamForm(matchId) }.getOrNull()
                MatchDetailsUiData(match = match, teamForm = teamForm)
            }.onSuccess { match ->
                _state.value = UiState.Success(match)
            }.onFailure { error ->
                _state.value = UiState.Error(error.message ?: "Unable to load match details")
            }
        }
    }
}

data class MatchDetailsUiData(
    val match: MatchDetailDto,
    val teamForm: MatchTeamFormDto?,
)
