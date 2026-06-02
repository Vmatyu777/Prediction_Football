package com.predictionfootball.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.predictionfootball.app.ui.components.StatusBadge
import com.predictionfootball.app.ui.theme.PredictionFootballTheme
import com.predictionfootball.app.viewmodel.AuthViewModel
import kotlinx.coroutines.delay

@Composable
fun SplashRoute(
    viewModel: AuthViewModel,
    onAuthenticated: () -> Unit,
    onUnauthenticated: () -> Unit,
) {
    LaunchedEffect(Unit) {
        delay(1200)
        viewModel.resolveStartupSession(
            onAuthenticated = onAuthenticated,
            onUnauthenticated = onUnauthenticated,
        )
    }

    SplashScreen()
}

@Composable
fun SplashScreen() {
    Surface(color = MaterialTheme.colorScheme.background) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            StatusBadge("Футбольный ИИ")
            Spacer(modifier = Modifier.height(18.dp))
            Text(
                text = "Футбольные прогнозы",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Black,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Прогнозы футбольных матчей",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Preview(showBackground = true, widthDp = 900)
@Composable
private fun SplashScreenPreview() {
    PredictionFootballTheme {
        SplashScreen()
    }
}
