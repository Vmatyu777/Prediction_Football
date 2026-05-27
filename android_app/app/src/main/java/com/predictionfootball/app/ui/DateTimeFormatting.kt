package com.predictionfootball.app.ui

import android.util.Log
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeFormatterBuilder
import java.time.temporal.ChronoField
import java.util.Locale

private const val DATE_TIME_TAG = "DateTimeFormatting"

private val BackendUtcDateTimeFormatter: DateTimeFormatter = DateTimeFormatterBuilder()
    .appendPattern("yyyy-MM-dd HH:mm:ss")
    .optionalStart()
    .appendFraction(ChronoField.NANO_OF_SECOND, 1, 9, true)
    .optionalEnd()
    .toFormatter(Locale.ROOT)

private val UserDateTimeFormatter: DateTimeFormatter =
    DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm", Locale("ru"))

fun formatBackendUtcDateTime(value: String): String {
    return runCatching {
        val rawValue = value.trim()
        val normalizedValue = rawValue.replace('T', ' ')
        val parsedUtc = LocalDateTime.parse(normalizedValue, BackendUtcDateTimeFormatter)
            .atOffset(ZoneOffset.UTC)
        val systemZone = ZoneId.systemDefault()
        val localDateTime = parsedUtc.atZoneSameInstant(systemZone)
        val formatted = localDateTime.format(UserDateTimeFormatter)

        Log.d(
            DATE_TIME_TAG,
            "raw createdAt=$rawValue, parsed UTC=$parsedUtc, system timezone=$systemZone, formatted local createdAt=$formatted",
        )
        formatted
    }.getOrElse { error ->
        Log.e(DATE_TIME_TAG, "Failed to parse backend UTC datetime: $value", error)
        "UTC: $value"
    }
}
