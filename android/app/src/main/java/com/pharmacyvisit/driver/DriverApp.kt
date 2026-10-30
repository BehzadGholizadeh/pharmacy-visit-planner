package com.pharmacyvisit.driver

import android.app.Application
import com.pharmacyvisit.driver.di.AppContainer
import com.pharmacyvisit.driver.di.DefaultAppContainer

class DriverApp : Application() {

    lateinit var appContainer: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        appContainer = DefaultAppContainer(applicationContext)
    }
}
