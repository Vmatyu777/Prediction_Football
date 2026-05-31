package com.predictionfootball.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.predictionfootball.app.models.AuthUserDto
import com.predictionfootball.app.models.PredictionHistoryDto
import com.predictionfootball.app.network.AuthRepository
import com.predictionfootball.app.network.AuthTokenStore
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.util.Locale

private const val SESSION_EXPIRED_MESSAGE = "Сессия истекла. Выполните вход повторно."
private const val MIN_PASSWORD_LENGTH = 8
private const val MAX_USERNAME_LENGTH = 50
private const val MIN_EMAIL_LENGTH = 5
private const val MAX_EMAIL_LENGTH = 100
private const val MAX_PASSWORD_LENGTH = 128
private const val LOGIN_RULE_MESSAGE = "Логин может содержать только латинские буквы, цифры, _ и -"
private const val LOGIN_LENGTH_MESSAGE = "Логин должен быть не длиннее 50 символов"
private const val EMAIL_RULE_MESSAGE = "Введите корректный email"
private const val EMAIL_LENGTH_MESSAGE = "Email должен содержать от 5 до 100 символов"
private const val PASSWORD_RULE_MESSAGE = "Пароль должен содержать минимум 8 символов, латинскую букву и цифру"
private const val PASSWORD_LENGTH_MESSAGE = "Пароль должен быть не длиннее 128 символов"

data class AuthFormState(
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

data class ProfileState(
    val user: AuthUserDto? = null,
    val history: List<PredictionHistoryDto> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

class AuthViewModel : ViewModel() {
    private val repository = AuthRepository()

    private val _formState = MutableStateFlow(AuthFormState())
    val formState: StateFlow<AuthFormState> = _formState.asStateFlow()

    private val _profileState = MutableStateFlow(ProfileState())
    val profileState: StateFlow<ProfileState> = _profileState.asStateFlow()

    val isAuthenticated: StateFlow<Boolean> = AuthTokenStore.isAuthenticated

    fun resolveStartupSession(
        onAuthenticated: () -> Unit,
        onUnauthenticated: () -> Unit,
    ) {
        if (AuthTokenStore.getAccessToken() == null) {
            onUnauthenticated()
            return
        }

        viewModelScope.launch {
            runCatching {
                repository.me()
            }.onSuccess {
                onAuthenticated()
            }.onFailure { error ->
                if (error.isAuthorizationFailure()) {
                    expireSession()
                } else {
                    repository.logout()
                }
                onUnauthenticated()
            }
        }
    }

    fun login(usernameOrEmail: String, password: String, onSuccess: () -> Unit) {
        if (usernameOrEmail.isBlank() || password.isBlank()) {
            _formState.value = AuthFormState(errorMessage = "Введите логин и пароль")
            return
        }

        _formState.value = AuthFormState(isLoading = true)
        viewModelScope.launch {
            runCatching {
                repository.login(usernameOrEmail.trim(), password)
            }.onSuccess {
                _formState.value = AuthFormState()
                onSuccess()
            }.onFailure { error ->
                _formState.value = AuthFormState(errorMessage = error.toAuthErrorMessage())
            }
        }
    }

    fun register(username: String, email: String, password: String, onSuccess: () -> Unit) {
        val validationError = validateRegistration(username, email, password)
        if (validationError != null) {
            _formState.value = AuthFormState(errorMessage = validationError)
            return
        }

        _formState.value = AuthFormState(isLoading = true)
        viewModelScope.launch {
            runCatching {
                repository.register(username.trim(), email.trim(), password)
                repository.login(username.trim(), password)
            }.onSuccess {
                _formState.value = AuthFormState()
                onSuccess()
            }.onFailure { error ->
                _formState.value = AuthFormState(errorMessage = error.toAuthErrorMessage())
            }
        }
    }

    fun loadProfile(onSessionExpired: () -> Unit = {}) {
        _profileState.value = _profileState.value.copy(isLoading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching {
                repository.me()
            }.onSuccess { user ->
                _profileState.value = _profileState.value.copy(
                    user = user,
                    isLoading = false,
                    errorMessage = null,
                )
            }.onFailure { error ->
                if (error.isAuthorizationFailure()) {
                    expireSession()
                    onSessionExpired()
                } else {
                    _profileState.value = _profileState.value.copy(
                        isLoading = false,
                        errorMessage = error.message ?: "Не удалось загрузить профиль",
                    )
                }
            }
        }
    }

    fun loadHistory(onSessionExpired: () -> Unit = {}) {
        _profileState.value = _profileState.value.copy(isLoading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching {
                repository.history()
            }.onSuccess { history ->
                _profileState.value = _profileState.value.copy(
                    history = history,
                    isLoading = false,
                    errorMessage = null,
                )
            }.onFailure { error ->
                if (error.isAuthorizationFailure()) {
                    expireSession()
                    onSessionExpired()
                } else {
                    _profileState.value = _profileState.value.copy(
                        isLoading = false,
                        errorMessage = error.message ?: "Не удалось загрузить историю",
                    )
                }
            }
        }
    }

    fun logout() {
        repository.logout()
        _profileState.value = ProfileState()
        _formState.value = AuthFormState()
    }

    private fun expireSession() {
        repository.logout()
        _profileState.value = ProfileState()
        _formState.value = AuthFormState(errorMessage = SESSION_EXPIRED_MESSAGE)
    }

    private fun Throwable.isAuthorizationFailure(): Boolean {
        return this is HttpException && (code() == 401 || code() == 403)
    }

    private fun validateRegistration(username: String, email: String, password: String): String? {
        val normalizedEmail = email.trim()
        return when {
            username.isBlank() -> "Введите логин"
            username.trim().length > MAX_USERNAME_LENGTH -> LOGIN_LENGTH_MESSAGE
            !username.trim().matches(Regex("^[A-Za-z0-9_-]+$")) -> LOGIN_RULE_MESSAGE
            normalizedEmail.isBlank() -> "Введите email"
            normalizedEmail.length !in MIN_EMAIL_LENGTH..MAX_EMAIL_LENGTH -> EMAIL_LENGTH_MESSAGE
            !normalizedEmail.matches(Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")) -> {
                EMAIL_RULE_MESSAGE
            }
            password.length < MIN_PASSWORD_LENGTH -> PASSWORD_RULE_MESSAGE
            password.length > MAX_PASSWORD_LENGTH -> PASSWORD_LENGTH_MESSAGE
            !password.matches(Regex("^[\\x21-\\x7E]+$")) -> PASSWORD_RULE_MESSAGE
            !password.any { it in 'A'..'Z' || it in 'a'..'z' } -> PASSWORD_RULE_MESSAGE
            !password.any { it.isDigit() } -> PASSWORD_RULE_MESSAGE
            else -> null
        }
    }

    private fun Throwable.toAuthErrorMessage(): String {
        if (this !is HttpException) {
            return message ?: "Не удалось выполнить запрос"
        }

        val body = response()?.errorBody()?.string().orEmpty().lowercase(Locale.ROOT)
        return when {
            code() == 409 && "username already exists" in body -> "Этот логин уже занят"
            code() == 409 && "email already exists" in body -> "Этот email уже зарегистрирован"
            "username" in body && "at most 50" in body -> LOGIN_LENGTH_MESSAGE
            "email" in body && ("at most 100" in body || "at least 5" in body) -> EMAIL_LENGTH_MESSAGE
            "password" in body && "at most 128" in body -> PASSWORD_LENGTH_MESSAGE
            "invalid email" in body -> EMAIL_RULE_MESSAGE
            "password must contain" in body || "string should have at least 8" in body -> PASSWORD_RULE_MESSAGE
            "username may contain" in body -> LOGIN_RULE_MESSAGE
            code() == 401 -> "Неверный логин или пароль"
            code() == 422 -> "Проверьте данные регистрации"
            else -> "Не удалось выполнить запрос"
        }
    }
}
