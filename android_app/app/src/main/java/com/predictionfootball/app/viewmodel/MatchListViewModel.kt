package com.predictionfootball.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.predictionfootball.app.models.MatchSummaryDto
import com.predictionfootball.app.network.PredictionRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

private const val DEFAULT_MATCH_CACHE_TTL_MILLIS = 5 * 60 * 1000L

enum class MatchListMode {
    Recent,
    Upcoming,
    Showcase,
}

class MatchListViewModel(
    private val cacheTtlMillis: Long = DEFAULT_MATCH_CACHE_TTL_MILLIS,
) : ViewModel() {
    private val repository = PredictionRepository()
    private val matchesCache = mutableMapOf<MatchListMode, CachedMatches>()
    private val loadingModes = mutableSetOf<MatchListMode>()
    private val ttlRefreshJobs = mutableMapOf<MatchListMode, Job>()

    private val _state = MutableStateFlow<UiState<List<MatchSummaryDto>>>(UiState.Loading)
    val state: StateFlow<UiState<List<MatchSummaryDto>>> = _state.asStateFlow()

    private val _mode = MutableStateFlow(MatchListMode.Upcoming)
    val mode: StateFlow<MatchListMode> = _mode.asStateFlow()

    private val _selectedLeague = MutableStateFlow<String?>(null)
    val selectedLeague: StateFlow<String?> = _selectedLeague.asStateFlow()

    private val _selectedSeason = MutableStateFlow<String?>(null)
    val selectedSeason: StateFlow<String?> = _selectedSeason.asStateFlow()

    private val _lastUpdatedAtMillis = MutableStateFlow<Long?>(null)
    val lastUpdatedAtMillis: StateFlow<Long?> = _lastUpdatedAtMillis.asStateFlow()

    init {
        loadMatches(MatchListMode.Upcoming)
    }

    fun loadMatches(mode: MatchListMode = _mode.value) {
        if (_mode.value != mode) {
            _selectedLeague.value = null
            _selectedSeason.value = null
        }
        _mode.value = mode

        val cachedMatches = matchesCache[mode]
        if (cachedMatches != null) {
            _lastUpdatedAtMillis.value = cachedMatches.loadedAtMillis
            _state.value = UiState.Success(cachedMatches.matches)
            if (cachedMatches.isExpired(cacheTtlMillis)) {
                fetchMatches(mode = mode, showLoading = false)
            }
            return
        }

        _lastUpdatedAtMillis.value = null
        fetchMatches(mode = mode, showLoading = true)
    }

    fun refreshStaleCurrentMode() {
        val mode = _mode.value
        val cachedMatches = matchesCache[mode] ?: return
        if (cachedMatches.isExpired(cacheTtlMillis)) {
            fetchMatches(mode = mode, showLoading = false)
        }
    }

    private fun fetchMatches(mode: MatchListMode, showLoading: Boolean) {
        if (!loadingModes.add(mode)) {
            return
        }
        if (showLoading) {
            _state.value = UiState.Loading
        }
        viewModelScope.launch {
            runCatching {
                when (mode) {
                    MatchListMode.Recent -> repository.recentMatches()
                    MatchListMode.Upcoming -> repository.upcomingMatches()
                    MatchListMode.Showcase -> repository.showcaseMatches()
                }
            }.onSuccess { matches ->
                val loadedAtMillis = System.currentTimeMillis()
                matchesCache[mode] = CachedMatches(matches = matches, loadedAtMillis = loadedAtMillis)
                scheduleTtlRefresh(mode)
                if (_mode.value == mode) {
                    _lastUpdatedAtMillis.value = loadedAtMillis
                    _state.value = UiState.Success(matches)
                }
            }.onFailure { error ->
                if (_mode.value == mode && showLoading) {
                    _state.value = UiState.Error(error.message ?: "Unable to load matches")
                }
            }.also {
                loadingModes.remove(mode)
            }
        }
    }

    private fun scheduleTtlRefresh(mode: MatchListMode) {
        ttlRefreshJobs[mode]?.cancel()
        ttlRefreshJobs[mode] = viewModelScope.launch {
            delay(cacheTtlMillis)
            if (_mode.value == mode) {
                refreshStaleCurrentMode()
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

private data class CachedMatches(
    val matches: List<MatchSummaryDto>,
    val loadedAtMillis: Long,
) {
    fun isExpired(cacheTtlMillis: Long, nowMillis: Long = System.currentTimeMillis()): Boolean {
        return nowMillis - loadedAtMillis >= cacheTtlMillis
    }
}
