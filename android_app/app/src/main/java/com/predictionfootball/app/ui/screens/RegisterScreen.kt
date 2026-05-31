package com.predictionfootball.app.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
    val context = LocalContext.current

    LaunchedEffect(state.errorMessage) {
        state.errorMessage?.let { message ->
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
        }
    }

    ScreenScaffold(
        title = "Регистрация",
        subtitle = "Создание аккаунта для истории прогнозов",
        modifier = Modifier
            .imePadding()
            .verticalScroll(rememberScrollState()),
    ) {
        InfoCard(modifier = Modifier.fillMaxWidth()) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
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
                    label = { Text("Email") },
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
                    text = if (state.isLoading) "Создание..." else "Зарегистрироваться",
                    onClick = { onRegister(username, email, password) },
                    modifier = Modifier.fillMaxWidth(),
                )
                TextButton(
                    onClick = onLoginClick,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Уже есть аккаунт")
                }
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
