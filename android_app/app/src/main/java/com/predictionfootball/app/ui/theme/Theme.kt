package com.predictionfootball.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val FootballPitchBlack = Color(0xFF050705)
val FootballSurface = Color(0xFF101410)
val FootballSurfaceHigh = Color(0xFF171D18)
val FootballLime = Color(0xFFD7FF35)
val FootballLimeSoft = Color(0xFF9FE870)
val FootballMuted = Color(0xFFA8B0A7)
val FootballLine = Color(0xFF2A332B)
val FootballWarning = Color(0xFFFFD166)
val FootballNegative = Color(0xFFFF6B6B)

private val DarkFootballColors = darkColorScheme(
    primary = FootballLime,
    onPrimary = Color(0xFF111600),
    primaryContainer = Color(0xFF263A09),
    onPrimaryContainer = FootballLime,
    secondary = FootballLimeSoft,
    onSecondary = Color(0xFF071006),
    secondaryContainer = Color(0xFF1C2D17),
    onSecondaryContainer = FootballLimeSoft,
    tertiary = FootballWarning,
    background = FootballPitchBlack,
    onBackground = Color(0xFFF3F7EF),
    surface = FootballSurface,
    onSurface = Color(0xFFF3F7EF),
    surfaceVariant = FootballSurfaceHigh,
    onSurfaceVariant = FootballMuted,
    outline = FootballLine,
    error = FootballNegative,
)

@Composable
fun PredictionFootballTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = DarkFootballColors,
        typography = MaterialTheme.typography,
        content = content,
    )
}
