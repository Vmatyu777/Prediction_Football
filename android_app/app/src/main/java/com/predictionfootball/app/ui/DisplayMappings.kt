package com.predictionfootball.app.ui

import java.util.Locale

fun displayMatchStatus(value: String): String = when (value.trim().lowercase(Locale.ROOT)) {
    "finished" -> "Завершен"
    "scheduled" -> "Запланирован"
    "postponed" -> "Перенесен"
    "cancelled" -> "Отменен"
    else -> value
}

fun displayOutcome(value: String): String = when (value.trim().uppercase(Locale.ROOT)) {
    "H" -> "П1"
    "D" -> "Н"
    "A" -> "П2"
    else -> value
}

fun displayBinaryLabel(value: String): String = when (value.trim().lowercase(Locale.ROOT)) {
    "yes" -> "Да"
    "no" -> "Нет"
    else -> value
}

fun displayProbabilityLabel(value: String): String = when (value.trim().uppercase(Locale.ROOT)) {
    "H", "D", "A" -> displayOutcome(value)
    "YES", "NO" -> displayBinaryLabel(value)
    "BTTS" -> "ОЗ"
    else -> value
}

fun displayBookmaker(value: String): String = when (value.trim().lowercase(Locale.ROOT)) {
    "market average", "average market odds" -> "Среднерыночные коэффициенты"
    else -> value
}
