package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import com.predictionfootball.app.models.AuthUserDto
import com.predictionfootball.app.ui.formatBackendUtcDateTime
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.PrimaryActionButton
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.AuthViewModel
import com.predictionfootball.app.viewmodel.ProfileState

@Composable
fun ProfileRoute(
    viewModel: AuthViewModel,
    onBack: () -> Unit,
    onHistoryClick: () -> Unit,
    onSessionExpired: () -> Unit,
    onLogout: () -> Unit,
) {
    val state by viewModel.profileState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadProfile(onSessionExpired)
    }

    ProfileScreen(
        state = state,
        onBack = onBack,
        onRetry = { viewModel.loadProfile(onSessionExpired) },
        onHistoryClick = onHistoryClick,
        onLogout = {
            viewModel.logout()
            onLogout()
        },
    )
}

@Composable
fun ProfileScreen(
    state: ProfileState,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onHistoryClick: () -> Unit,
    onLogout: () -> Unit,
) {
    ScreenScaffold(
        title = "Профиль",
        subtitle = "Данные пользователя",
        modifier = Modifier.verticalScroll(rememberScrollState()),
        actions = {
            OutlinedButton(onClick = onBack) {
                Text("К матчам")
            }
        },
    ) {
        when {
            state.isLoading && state.user == null -> LoadingContent("Загрузка профиля")
            state.errorMessage != null && state.user == null -> ErrorContent(
                message = state.errorMessage,
                onRetry = onRetry,
            )
            state.user != null -> ProfileContent(
                state = state,
                onHistoryClick = onHistoryClick,
                onLogout = onLogout,
            )
        }
    }
}

@Composable
private fun ProfileContent(
    state: ProfileState,
    onHistoryClick: () -> Unit,
    onLogout: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            ProfileField("Логин", state.user?.username.orEmpty())
            Spacer(modifier = Modifier.height(8.dp))
            ProfileField("Email", state.user?.email.orEmpty())
            Spacer(modifier = Modifier.height(8.dp))
            ProfileField("Роль", state.user?.role.orEmpty())
            Spacer(modifier = Modifier.height(8.dp))
            ProfileField("Создан", formatBackendUtcDateTime(state.user?.createdAt.orEmpty()))
        }
        PrimaryActionButton(
            text = "История прогнозов",
            onClick = onHistoryClick,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedButton(onClick = onLogout, modifier = Modifier.fillMaxWidth()) {
            Text("Выйти")
        }
    }
}

@Composable
private fun ProfileField(label: String, value: String) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = value,
            modifier = Modifier.fillMaxWidth(),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun ProfileScreenPreview() {
    PredictionFootballTheme {
        ProfileScreen(
            state = ProfileState(
                user = AuthUserDto(
                    id = 1,
                    username = "student",
                    email = "student@example.com",
                    role = "user",
                    createdAt = "2026-05-27T16:55:00.123456",
                ),
            ),
            onBack = {},
            onRetry = {},
            onHistoryClick = {},
            onLogout = {},
        )
    }
}
