package com.predictionfootball.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.predictionfootball.app.models.MatchSummaryDto
import com.predictionfootball.app.network.PredictionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class MatchListMode {
    Recent,
    Upcoming,
    Showcase,
}

class MatchListViewModel(
) : ViewModel() {
    private val repository = PredictionRepository()

    private val _state = MutableStateFlow<UiState<List<MatchSummaryDto>>>(UiState.Loading)
    val state: StateFlow<UiState<List<MatchSummaryDto>>> = _state.asStateFlow()

    private val _mode = MutableStateFlow(MatchListMode.Recent)
    val mode: StateFlow<MatchListMode> = _mode.asStateFlow()

    private val _selectedLeague = MutableStateFlow<String?>(null)
    val selectedLeague: StateFlow<String?> = _selectedLeague.asStateFlow()

    private val _selectedSeason = MutableStateFlow<String?>(null)
    val selectedSeason: StateFlow<String?> = _selectedSeason.asStateFlow()

    init {
        loadMatches(MatchListMode.Recent)
    }

    fun loadMatches(mode: MatchListMode = _mode.value) {
        if (_mode.value != mode) {
            _selectedLeague.value = null
            _selectedSeason.value = null
        }
        _mode.value = mode
        _state.value = UiState.Loading
        viewModelScope.launch {
            runCatching {
                when (mode) {
                    MatchListMode.Recent -> repository.recentMatches()
                    MatchListMode.Upcoming -> repository.upcomingMatches()
                    MatchListMode.Showcase -> repository.showcaseMatches()
                }
            }.onSuccess { matches ->
                _state.value = UiState.Success(matches)
            }.onFailure { error ->
                _state.value = UiState.Error(error.message ?: "Unable to load matches")
            }
        }
    }

    fun selectLeague(league: String?) {
        _selectedLeague.value = league
    }

    fun selectSeason(season: String?) {
        _selectedSeason.value = season
    }
}
