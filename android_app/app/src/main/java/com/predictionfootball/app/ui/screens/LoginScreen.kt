package com.predictionfootball.app.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.ui.components.InfoCard
import com.predictionfootball.app.ui.components.PrimaryActionButton
import com.predictionfootball.app.ui.components.ScreenScaffold
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.AuthFormState
import com.predictionfootball.app.viewmodel.AuthViewModel

@Composable
fun LoginRoute(
    viewModel: AuthViewModel,
    onLoginSuccess: () -> Unit,
    onRegisterClick: () -> Unit,
) {
    val state by viewModel.formState.collectAsState()

    LoginScreen(
        state = state,
        onLogin = { usernameOrEmail, password ->
            viewModel.login(usernameOrEmail, password, onLoginSuccess)
        },
        onRegisterClick = onRegisterClick,
    )
}

@Composable
fun LoginScreen(
    state: AuthFormState,
    onLogin: (String, String) -> Unit,
    onRegisterClick: () -> Unit,
) {
    var usernameOrEmail by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    val context = LocalContext.current

    LaunchedEffect(state.errorMessage) {
        state.errorMessage?.let { message ->
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
        }
    }

    ScreenScaffold(
        title = "Вход",
        subtitle = "Авторизация пользователя",
        modifier = Modifier
            .imePadding()
            .verticalScroll(rememberScrollState()),
    ) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = usernameOrEmail,
                    onValueChange = { usernameOrEmail = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Логин или email") },
                    singleLine = true,
                )
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Пароль") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                )
                PrimaryActionButton(
                    text = if (state.isLoading) "Вход..." else "Войти",
                    onClick = { onLogin(usernameOrEmail, password) },
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(modifier = Modifier.height(4.dp))
                OutlinedButton(
                    onClick = onRegisterClick,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Создать аккаунт")
                }
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun LoginScreenPreview() {
    PredictionFootballTheme {
        LoginScreen(
            state = AuthFormState(),
            onLogin = { _, _ -> },
            onRegisterClick = {},
        )
    }
}
