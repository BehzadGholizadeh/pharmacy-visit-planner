package com.pharmacyvisit.driver.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.CreationExtras

/**
 * Lightweight factory for constructor-injected ViewModels.
 *
 * Dependencies are supplied by AppContainer/repositories; CreationExtras remains available
 * for SavedStateHandle-aware ViewModels without introducing a DI framework.
 */
class AppViewModelFactory<VM : ViewModel>(
    private val creator: (CreationExtras) -> VM
) : ViewModelProvider.Factory {

    override fun <T : ViewModel> create(
        modelClass: Class<T>,
        extras: CreationExtras
    ): T {
        val viewModel = creator(extras)
        require(modelClass.isInstance(viewModel)) {
            "Factory created ${viewModel::class.java.name}, expected ${modelClass.name}."
        }

        @Suppress("UNCHECKED_CAST")
        return viewModel as T
    }
}
