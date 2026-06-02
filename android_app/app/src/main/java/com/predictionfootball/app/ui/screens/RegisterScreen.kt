package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.zIndex
import com.predictionfootball.app.R
import com.predictionfootball.app.ui.components.InAppNotification
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.PrimaryActionButton
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.components.SecondaryActionButton
import com.predictionfootball.app.ui.components.StatusBadge
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.AuthFormState
import com.predictionfootball.app.viewmodel.AuthViewModel
import kotlinx.coroutines.delay

@Composable
fun RegisterRoute(
    viewModel: AuthViewModel,
    onRegisterSuccess: () -> Unit,
    onLoginClick: () -> Unit,
) {
    val state by viewModel.formState.collectAsState()

    RegisterScreen(
        state = state,
        onRegister = { username, email, password ->
            viewModel.register(username, email, password, onRegisterSuccess)
        },
        onLoginClick = onLoginClick,
    )
}

@Composable
fun RegisterScreen(
    state: AuthFormState,
    onRegister: (String, String, String) -> Unit,
    onLoginClick: () -> Unit,
) {
    var username by rememberSaveable { mutableStateOf("") }
    var email by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var passwordVisible by rememberSaveable { mutableStateOf(false) }
    var visibleError by rememberSaveable { mutableStateOf<String?>(null) }
    var submitAttempt by rememberSaveable { mutableStateOf(0) }

    LaunchedEffect(submitAttempt, state.errorMessage, state.isLoading) {
        if (state.isLoading) {
            visibleError = null
            return@LaunchedEffect
        }
        if (submitAttempt > 0 && !state.isLoading && state.errorMessage != null) {
            visibleError = state.errorMessage
            delay(2700)
            visibleError = null
        }
    }

    ScreenScaffold(
        title = "Регистрация",
        subtitle = "Аккаунт для сохранения истории прогнозов",
        modifier = Modifier
            .imePadding()
            .verticalScroll(rememberScrollState()),
    ) {
        BoxWithConstraints(
            modifier = Modifier.fillMaxWidth(),
            contentAlignment = Alignment.TopCenter,
        ) {
            val notificationAlignment = if (maxWidth >= 640.dp) Alignment.TopEnd else Alignment.TopCenter
            InfoCard(modifier = Modifier.widthIn(max = 540.dp).fillMaxWidth()) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    StatusBadge("Аккаунт пользователя")
                    OutlinedTextField(
                        value = username,
                        onValueChange = { username = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Логин") },
                        singleLine = true,
                    )
                    OutlinedTextField(
                        value = email,
                        onValueChange = { email = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Эл. почта") },
                        singleLine = true,
                    )
                    OutlinedTextField(
                        value = password,
                        onValueChange = { password = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Пароль") },
                        singleLine = true,
                        visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                        trailingIcon = {
                            IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                Icon(
                                    painter = painterResource(
                                        if (passwordVisible) {
                                            R.drawable.ic_visibility_off_24
                                        } else {
                                            R.drawable.ic_visibility_24
                                        },
                                    ),
                                    contentDescription = if (passwordVisible) "Скрыть пароль" else "Показать пароль",
                                )
                            }
                        },
                    )
                    PrimaryActionButton(
                        text = if (state.isLoading) "Создание..." else "Зарегистрироваться",
                        onClick = {
                            submitAttempt += 1
                            onRegister(username, email, password)
                        },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    SecondaryActionButton(
                        text = "Уже есть аккаунт",
                        onClick = onLoginClick,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
            visibleError?.let { message ->
                InAppNotification(
                    message = message,
                    modifier = Modifier
                        .align(notificationAlignment)
                        .widthIn(max = 340.dp)
                        .padding(top = 4.dp)
                        .zIndex(1f),
                )
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun RegisterScreenPreview() {
    PredictionFootballTheme {
        RegisterScreen(
            state = AuthFormState(),
            onRegister = { _, _, _ -> },
            onLoginClick = {},
        )
    }
}
