package com.predictionfootball.app.ui

import java.util.Locale

fun displayMatchStatus(value: String): String = when (value.trim().lowercase(Locale.ROOT)) {
    "finished" -> "Завершен"
    "scheduled" -> "Запланирован"
    "postponed" -> "Перенесен"
    "cancelled" -> "Отменен"
    else -> value
}

fun displayMatchSource(value: String): String = when (value.trim().lowercase(Locale.ROOT)) {
    "historical" -> ""
    "demo" -> "Демо-матч"
    "api" -> "Матч API"
    else -> value
}

fun displayOutcomeLong(value: String): String = when (value.trim().uppercase(Locale.ROOT)) {
    "H" -> "Победа хозяев"
    "D" -> "Ничья"
    "A" -> "Победа гостей"
    else -> value
}

fun displayBinaryLabel(value: String): String = when (value.trim().lowercase(Locale.ROOT)) {
    "yes" -> "Да"
    "no" -> "Нет"
    else -> value
}

fun displayProbabilityLabel(value: String): String = when (value.trim().uppercase(Locale.ROOT)) {
    "H", "D", "A" -> displayOutcomeLong(value)
    "YES", "NO" -> displayBinaryLabel(value)
    "BTTS" -> "ОЗ"
    else -> value
}

fun displayBookmaker(value: String): String = when (value.trim().lowercase(Locale.ROOT)) {
    "market average", "average market odds" -> "Среднерыночные коэффициенты"
    else -> value
}
