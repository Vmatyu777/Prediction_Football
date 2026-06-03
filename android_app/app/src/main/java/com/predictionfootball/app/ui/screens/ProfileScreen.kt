package com.predictionfootball.app.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.spring
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.models.AuthUserDto
import com.predictionfootball.app.ui.formatBackendUtcDateTime
import com.predictionfootball.app.ui.components.ErrorContent
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.LoadingContent
import com.predictionfootball.app.ui.components.PrimaryActionButton
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.components.SecondaryActionButton
import com.predictionfootball.app.ui.components.StatusBadge
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
        onHistoryClick = {
            viewModel.openHistoryWithFreshUnreadCount(
                onReady = onHistoryClick,
                onSessionExpired = onSessionExpired,
            )
        },
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
        subtitle = "Аккаунт и сохранённая аналитика",
        modifier = Modifier.verticalScroll(rememberScrollState()),
        actions = {
            OutlinedButton(
                onClick = onLogout,
                modifier = Modifier.height(48.dp),
                shape = RoundedCornerShape(14.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.error.copy(alpha = 0.55f)),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.error,
                ),
            ) {
                Text("Выйти")
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
                onBack = onBack,
                onHistoryClick = onHistoryClick,
            )
            state.showProfileFallback -> ProfileFallbackContent(onBack = onBack, onRetry = onRetry)
            else -> Unit
        }
    }
}

@Composable
private fun ProfileFallbackContent(
    onBack: () -> Unit,
    onRetry: () -> Unit,
) {
    Box(
        modifier = Modifier.fillMaxWidth(),
        contentAlignment = androidx.compose.ui.Alignment.TopCenter,
    ) {
        InfoCard(modifier = Modifier.widthIn(max = 540.dp).fillMaxWidth()) {
            Text(
                text = "Профиль не загружен",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Не удалось получить данные пользователя",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(modifier = Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                PrimaryActionButton(
                    text = "Обновить",
                    onClick = onRetry,
                    modifier = Modifier.weight(1f),
                )
                SecondaryActionButton(
                    text = "К матчам",
                    onClick = onBack,
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }
}
@Composable
private fun ProfileContent(
    state: ProfileState,
    onBack: () -> Unit,
    onHistoryClick: () -> Unit,
) {
    Box(
        modifier = Modifier.fillMaxWidth(),
        contentAlignment = androidx.compose.ui.Alignment.TopCenter,
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = 820.dp)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            InfoCard(modifier = Modifier.fillMaxWidth()) {
                BoxWithConstraints {
                    val compact = maxWidth < 620.dp
                    if (compact) {
                        Column(verticalArrangement = Arrangement.spacedBy(18.dp)) {
                            UserIdentity(state)
                            StatusBadge("Вход выполнен")
                            ProfileField("Роль", displayUserRole(state.user?.role.orEmpty()))
                            ProfileField("Создан", formatBackendUtcDateTime(state.user?.createdAt.orEmpty()))
                        }
                    } else {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
                        ) {
                            UserIdentity(
                                state = state,
                                modifier = Modifier.weight(1f),
                            )
                            Column(
                                modifier = Modifier.weight(1f),
                                horizontalAlignment = androidx.compose.ui.Alignment.End,
                                verticalArrangement = Arrangement.spacedBy(14.dp),
                            ) {
                                StatusBadge("Вход выполнен")
                                ProfileField(
                                    label = "Роль",
                                    value = displayUserRole(state.user?.role.orEmpty()),
                                    modifier = Modifier.widthIn(max = 320.dp),
                                    compact = true,
                                )
                                ProfileField(
                                    label = "Создан",
                                    value = formatBackendUtcDateTime(state.user?.createdAt.orEmpty()),
                                    modifier = Modifier.widthIn(max = 320.dp),
                                    compact = true,
                                )
                            }
                        }
                    }
                }
            }
            BoxWithConstraints(
                modifier = Modifier.fillMaxWidth(),
                contentAlignment = androidx.compose.ui.Alignment.Center,
            ) {
                if (maxWidth < 420.dp) {
                    Column(
                        modifier = Modifier.widthIn(max = 360.dp).fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        HistoryActionButton(
                            newPredictionsCount = state.newPredictionsCount,
                            onClick = onHistoryClick,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        SecondaryActionButton(
                            text = "К матчам",
                            onClick = onBack,
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                } else {
                    Row(
                        modifier = Modifier.widthIn(max = 640.dp).fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        HistoryActionButton(
                            newPredictionsCount = state.newPredictionsCount,
                            onClick = onHistoryClick,
                            modifier = Modifier.weight(1f),
                        )
                        SecondaryActionButton(
                            text = "К матчам",
                            onClick = onBack,
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HistoryActionButton(
    newPredictionsCount: Int,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(modifier = modifier.animateContentSize()) {
        PrimaryActionButton(
            text = "История",
            onClick = onClick,
            modifier = Modifier.fillMaxWidth(),
        )
        AnimatedVisibility(
            visible = newPredictionsCount > 0,
            modifier = Modifier
                .align(androidx.compose.ui.Alignment.CenterEnd)
                .padding(end = 12.dp),
            enter = fadeIn() + scaleIn(animationSpec = spring(), initialScale = 0.85f),
            exit = fadeOut() + scaleOut(targetScale = 0.85f),
        ) {
            StatusBadge(
                text = newPredictionsCount.coerceAtMost(99).toString(),
                accent = MaterialTheme.colorScheme.onPrimary,
            )
        }
    }
}

@Composable
private fun UserIdentity(state: ProfileState, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier,
        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
    ) {
        UserAvatar(state.user?.username.orEmpty())
        Spacer(modifier = Modifier.width(16.dp))
        Column {
            Text(
                text = state.user?.username.orEmpty(),
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Black,
            )
            Text(
                text = state.user?.email.orEmpty(),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun ProfileField(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    compact: Boolean = false,
) {
    if (compact) {
        Row(
            modifier = modifier.padding(vertical = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(18.dp),
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = value,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.SemiBold,
                textAlign = TextAlign.End,
            )
        }
        return
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = value,
            modifier = Modifier.weight(1.4f),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.SemiBold,
            textAlign = TextAlign.End,
        )
    }
}

private fun displayUserRole(value: String): String = when (value.trim().lowercase()) {
    "user" -> "Пользователь"
    "admin" -> "Администратор"
    else -> value
}

@Composable
private fun UserAvatar(username: String) {
    Surface(
        modifier = Modifier
            .size(58.dp)
            .clip(CircleShape),
        shape = CircleShape,
        color = MaterialTheme.colorScheme.primary.copy(alpha = 0.14f),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.45f)),
    ) {
        Box(contentAlignment = androidx.compose.ui.Alignment.Center) {
            Text(
                text = username.firstOrNull()?.uppercaseChar()?.toString() ?: "П",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Black,
            )
        }
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
