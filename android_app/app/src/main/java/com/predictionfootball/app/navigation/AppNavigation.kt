package com.predictionfootball.app.navigation

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.predictionfootball.app.ui.screens.HistoryRoute
import com.predictionfootball.app.ui.screens.LoginRoute
import com.predictionfootball.app.ui.screens.MatchDetailsRoute
import com.predictionfootball.app.ui.screens.MatchListRoute
import com.predictionfootball.app.ui.screens.PredictionRoute
import com.predictionfootball.app.ui.screens.ProfileRoute
import com.predictionfootball.app.ui.screens.RegisterRoute
import com.predictionfootball.app.ui.screens.SplashRoute
import com.predictionfootball.app.viewmodel.AuthViewModel

private object Routes {
    const val Login = "login"
    const val Splash = "splash"
    const val Register = "register"
    const val MatchList = "matches"
    const val MatchDetails = "matches/{matchId}"
    const val Prediction = "matches/{matchId}/prediction"
    const val Profile = "profile"
    const val History = "history"

    fun matchDetails(matchId: Long) = "matches/$matchId"
    fun prediction(matchId: Long) = "matches/$matchId/prediction"
}

@Composable
fun PredictionFootballNavHost() {
    val navController = rememberNavController()
    val authViewModel: AuthViewModel = viewModel()
    val navigateToLogin: () -> Unit = {
        navController.navigate(Routes.Login) {
            popUpTo(Routes.Splash) { inclusive = true }
            launchSingleTop = true
        }
    }

    NavHost(
        navController = navController,
        startDestination = Routes.Splash,
    ) {
        composable(Routes.Splash) {
            SplashRoute(
                viewModel = authViewModel,
                onAuthenticated = {
                    navController.navigate(Routes.MatchList) {
                        popUpTo(Routes.Splash) { inclusive = true }
                    }
                },
                onUnauthenticated = {
                    navController.navigate(Routes.Login) {
                        popUpTo(Routes.Splash) { inclusive = true }
                    }
                },
            )
        }
        composable(Routes.Login) {
            LoginRoute(
                viewModel = authViewModel,
                onLoginSuccess = {
                    navController.navigate(Routes.MatchList) {
                        popUpTo(Routes.Login) { inclusive = true }
                    }
                },
                onRegisterClick = { navController.navigate(Routes.Register) },
            )
        }
        composable(Routes.Register) {
            RegisterRoute(
                viewModel = authViewModel,
                onRegisterSuccess = {
                    navController.navigate(Routes.MatchList) {
                        popUpTo(Routes.Login) { inclusive = true }
                    }
                },
                onLoginClick = { navController.popBackStack() },
            )
        }
        composable(Routes.MatchList) {
            MatchListRoute(
                viewModel = viewModel(),
                onMatchClick = { matchId -> navController.navigate(Routes.matchDetails(matchId)) },
                onProfileClick = { navController.navigate(Routes.Profile) },
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
        composable(Routes.Profile) {
            ProfileRoute(
                viewModel = authViewModel,
                onBack = { navController.popBackStack() },
                onHistoryClick = { navController.navigate(Routes.History) },
                onSessionExpired = navigateToLogin,
                onLogout = navigateToLogin,
            )
        }
        composable(Routes.History) {
            HistoryRoute(
                viewModel = authViewModel,
                onBack = { navController.popBackStack() },
                onSessionExpired = navigateToLogin,
            )
        }
    }
}
