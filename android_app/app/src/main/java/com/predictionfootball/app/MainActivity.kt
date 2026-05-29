package com.predictionfootball.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.predictionfootball.app.navigation.PredictionFootballNavHost
import com.predictionfootball.app.network.AuthTokenStore
import com.predictionfootball.app.ui.theme.PredictionFootballTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        AuthTokenStore.initialize(applicationContext)
        setContent {
            PredictionFootballTheme {
                PredictionFootballNavHost()
            }
        }
    }
}
