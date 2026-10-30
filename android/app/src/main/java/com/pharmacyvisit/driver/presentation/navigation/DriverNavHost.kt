package com.pharmacyvisit.driver.presentation.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.pharmacyvisit.driver.presentation.login.LoginScreen
import com.pharmacyvisit.driver.presentation.today.TodayRouteScreen

object Routes {
    const val LOGIN = "login"
    const val TODAY = "today"
    const val STOP_DETAIL = "stop/{stopId}"
}

@Composable
fun DriverNavHost() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = Routes.LOGIN
    ) {
        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Routes.TODAY) {
                        popUpTo(Routes.LOGIN) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.TODAY) {
            TodayRouteScreen(
                onStopClick = { stopId ->
                    navController.navigate("stop/$stopId")
                }
            )
        }
        // Stop detail will be added in next Gemini step
    }
}
