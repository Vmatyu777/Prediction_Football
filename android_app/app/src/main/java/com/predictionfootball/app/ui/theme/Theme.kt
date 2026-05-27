package com.predictionfootball.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = Color(0xFF176B4D),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD8F2E6),
    onPrimaryContainer = Color(0xFF0F3F2E),
    secondary = Color(0xFF385A7C),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFDCEAF8),
    onSecondaryContainer = Color(0xFF17324D),
    tertiary = Color(0xFF8A5A1F),
    background = Color(0xFFF7FAF7),
    surface = Color(0xFFFFFFFF),
    surfaceVariant = Color(0xFFE4EAE5),
    outline = Color(0xFF768178),
)

@Composable
fun PredictionFootballTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = LightColors,
        typography = MaterialTheme.typography,
        content = content,
    )
}
