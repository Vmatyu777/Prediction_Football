package com.predictionfootball.app.navigation

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.predictionfootball.app.ui.screens.MatchDetailsRoute
import com.predictionfootball.app.ui.screens.MatchListRoute
import com.predictionfootball.app.ui.screens.PredictionRoute

private object Routes {
    const val MatchList = "matches"
    const val MatchDetails = "matches/{matchId}"
    const val Prediction = "matches/{matchId}/prediction"

    fun matchDetails(matchId: Long) = "matches/$matchId"
    fun prediction(matchId: Long) = "matches/$matchId/prediction"
}

@Composable
fun PredictionFootballNavHost() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = Routes.MatchList,
    ) {
        composable(Routes.MatchList) {
            MatchListRoute(
                viewModel = viewModel(),
                onMatchClick = { matchId -> navController.navigate(Routes.matchDetails(matchId)) },
            )
        }
        composable(
            route = Routes.MatchDetails,
            arguments = listOf(navArgument("matchId") { type = NavType.LongType }),
        ) {
            MatchDetailsRoute(
                viewModel = viewModel(),
                onBack = { navController.popBackStack() },
                onGeneratePrediction = { matchId -> navController.navigate(Routes.prediction(matchId)) },
            )
        }
        composable(
            route = Routes.Prediction,
            arguments = listOf(navArgument("matchId") { type = NavType.LongType }),
        ) {
            PredictionRoute(
                viewModel = viewModel(),
                onBack = { navController.popBackStack() },
            )
        }
    }
}
