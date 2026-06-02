package com.predictionfootball.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.ui.graphics.toArgb
import com.predictionfootball.app.navigation.PredictionFootballNavHost
import com.predictionfootball.app.network.AuthTokenStore
import com.predictionfootball.app.ui.theme.FootballPitchBlack
import com.predictionfootball.app.ui.theme.PredictionFootballTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = FootballPitchBlack.toArgb()
        window.navigationBarColor = FootballPitchBlack.toArgb()
        AuthTokenStore.initialize(applicationContext)
        setContent {
            PredictionFootballTheme {
                PredictionFootballNavHost()
            }
        }
    }
}
