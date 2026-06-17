# SQLAdmin Audit

This document audits the SQLAdmin model views configured for the production administration panel.

The audit focuses on visible fields, details coverage, edit/create exposure, filters/search, and foreign-key coverage. It does not change database schema, backend API contracts, or ML logic.

## users

SQLAdmin view: `UserAdmin`
Model class: `User`
Create/Edit/Delete: create=False, edit=True, delete=False

Database columns: `id, username, email, password_hash, created_at, last_history_viewed_at, role_id`
Relationships: `role, query_history`
List view fields: `id, username, email, role, created_at, last_history_viewed_at`
Detail view fields: `id, username, email, role, created_at, last_history_viewed_at`
Create/Edit form fields: `role`
Search fields: `username, email`
Filters: `Роль`

Database columns not explicitly shown in list/detail fields: `password_hash, role_id`
Columns intentionally omitted from compact list view: `password_hash, role_id`


## user_roles

SQLAdmin view: `UserRoleAdmin`
Model class: `UserRole`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `users`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## matches

SQLAdmin view: `MatchAdmin`
Model class: `Match`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, match_date, season_id, home_team_id, away_team_id, status_id, source_id, external_source_id, external_match_id, last_synced_at`
Relationships: `season, home_team, away_team, status, source, external_source, result, odds, predictions`
List view fields: `id, match_date, season, home_team, away_team, status, source, external_match_id`
Detail view fields: `id, match_date, season, home_team, away_team, status, source, external_source, external_match_id, last_synced_at`
Create/Edit form fields: `none`
Search fields: `external_match_id`
Filters: `Сезон, Статус, Источник, Внешний источник`
Filter note: the `Сезон` filter displays season options as `League - season` to distinguish same-named seasons across leagues.

Database columns not explicitly shown in list/detail fields: `season_id, home_team_id, away_team_id, status_id, source_id, external_source_id`
Columns intentionally omitted from compact list view: `season_id, home_team_id, away_team_id, status_id, source_id, external_source_id, last_synced_at`


## match_results

SQLAdmin view: `MatchResultAdmin`
Model class: `MatchResult`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, actual_outcome, home_goals, away_goals, total_corners, total_yellow_cards, match_id`
Relationships: `match`
List view fields: `id, match_id, actual_outcome, home_goals, away_goals, total_corners, total_yellow_cards`
Detail view fields: `id, match_id, actual_outcome, home_goals, away_goals, total_corners, total_yellow_cards`
Create/Edit form fields: `none`
Search fields: `none`
Filters: `Исход`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## odds

SQLAdmin view: `OddsAdmin`
Model class: `Odds`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, home_win_odds, draw_odds, away_win_odds, over25_odds, under25_odds, collected_at, match_id, bookmaker_id`
Relationships: `match, bookmaker`
List view fields: `id, match_id, bookmaker, home_win_odds, draw_odds, away_win_odds, over25_odds, under25_odds, collected_at`
Detail view fields: `id, match_id, bookmaker, home_win_odds, draw_odds, away_win_odds, over25_odds, under25_odds, collected_at`
Create/Edit form fields: `none`
Search fields: `none`
Filters: `Букмекер`

Database columns not explicitly shown in list/detail fields: `bookmaker_id`
Columns intentionally omitted from compact list view: `bookmaker_id`


## predictions

SQLAdmin view: `PredictionAdmin`
Model class: `Prediction`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, created_at, predicted_outcome, home_win_probability, draw_probability, away_win_probability, model_id, match_id`
Relationships: `model, match, characteristic_values, query_history`
List view fields: `id, created_at, match, model, predicted_outcome, home_win_probability, draw_probability, away_win_probability`
Detail view fields: `id, created_at, match, model, predicted_outcome, home_win_probability, draw_probability, away_win_probability`
Create/Edit form fields: `none`
Search fields: `none`
Filters: `Модель, Исход`

Database columns not explicitly shown in list/detail fields: `model_id, match_id`
Columns intentionally omitted from compact list view: `model_id, match_id`


## prediction_characteristic_values

SQLAdmin view: `PredictionCharacteristicValueAdmin`
Model class: `PredictionCharacteristicValue`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `prediction_id, characteristic_id, predicted_value, probability`
Relationships: `prediction, characteristic`
List view fields: `prediction_id, characteristic_id, predicted_value, probability`
Detail view fields: `prediction_id, characteristic_id, predicted_value, probability`
Create/Edit form fields: `none`
Search fields: `none`
Filters: `Характеристика`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## user_query_history

SQLAdmin view: `UserQueryHistoryAdmin`
Model class: `UserQueryHistory`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, query_date, user_id, prediction_id`
Relationships: `user, prediction`
List view fields: `id, query_date, user, prediction`
Detail view fields: `id, query_date, user, prediction`
Create/Edit form fields: `none`
Search fields: `none`
Filters: `Пользователь`

Database columns not explicitly shown in list/detail fields: `user_id, prediction_id`
Columns intentionally omitted from compact list view: `user_id, prediction_id`


## models

SQLAdmin view: `ModelAdmin`
Model class: `Model`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name, version, trained_at, file_path, model_type_id`
Relationships: `model_type, metrics, predictions`
List view fields: `id, name, version, trained_at, file_path, model_type`
Detail view fields: `id, name, version, trained_at, file_path, model_type`
Create/Edit form fields: `none`
Search fields: `name, version, file_path`
Filters: `Тип модели`

Database columns not explicitly shown in list/detail fields: `model_type_id`
Columns intentionally omitted from compact list view: `model_type_id`


## model_metrics

SQLAdmin view: `ModelMetricAdmin`
Model class: `ModelMetric`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `model_id, metric_id, metric_value, is_primary`
Relationships: `model, metric`
List view fields: `model_id, metric_id, metric_value, is_primary`
Detail view fields: `model_id, metric_id, metric_value, is_primary`
Create/Edit form fields: `none`
Search fields: `none`
Filters: `Модель, Метрика, Основная`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## countries

SQLAdmin view: `CountryAdmin`
Model class: `Country`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `leagues, teams`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## leagues

SQLAdmin view: `LeagueAdmin`
Model class: `League`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name, country_id`
Relationships: `country, seasons`
List view fields: `id, name, country`
Detail view fields: `id, name, country`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `Страна`

Database columns not explicitly shown in list/detail fields: `country_id`
Columns intentionally omitted from compact list view: `country_id`


## seasons

SQLAdmin view: `SeasonAdmin`
Model class: `Season`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name, start_date, end_date, league_id`
Relationships: `league, matches`
List view fields: `id, name, start_date, end_date, league`
Detail view fields: `id, name, start_date, end_date, league`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `Лига`

Database columns not explicitly shown in list/detail fields: `league_id`
Columns intentionally omitted from compact list view: `league_id`


## teams

SQLAdmin view: `TeamAdmin`
Model class: `Team`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name, country_id`
Relationships: `country, elo_ratings, home_matches, away_matches`
List view fields: `id, name, country`
Detail view fields: `id, name, country`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `Страна`

Database columns not explicitly shown in list/detail fields: `country_id`
Columns intentionally omitted from compact list view: `country_id`


## team_elo_ratings

SQLAdmin view: `TeamEloRatingAdmin`
Model class: `TeamEloRating`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, rating_date, elo_value, team_id`
Relationships: `team`
List view fields: `id, rating_date, team, elo_value`
Detail view fields: `id, rating_date, team, team_id, elo_value`
Create/Edit form fields: `none`
Search fields: `none`
Filters: `Команда`

All database columns are represented directly or through configured list/detail relationship fields.
Columns intentionally omitted from compact list view: `team_id`


## metrics

SQLAdmin view: `MetricAdmin`
Model class: `Metric`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `model_metrics`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## model_types

SQLAdmin view: `ModelTypeAdmin`
Model class: `ModelType`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `models`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## match_sources

SQLAdmin view: `MatchSourceAdmin`
Model class: `MatchSource`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `matches`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## external_sources

SQLAdmin view: `ExternalSourceAdmin`
Model class: `ExternalSource`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `matches`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## bookmakers

SQLAdmin view: `BookmakerAdmin`
Model class: `Bookmaker`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `odds`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## prediction_characteristics

SQLAdmin view: `PredictionCharacteristicAdmin`
Model class: `PredictionCharacteristic`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `values`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## match_statuses

SQLAdmin view: `MatchStatusAdmin`
Model class: `MatchStatus`
Create/Edit/Delete: create=False, edit=False, delete=False

Database columns: `id, name`
Relationships: `matches`
List view fields: `id, name`
Detail view fields: `id, name`
Create/Edit form fields: `none`
Search fields: `name`
Filters: `none`

All database columns are represented directly or through configured list/detail relationship fields.
The compact list view includes all database columns.


## Audit Summary

- `matches` already exposes source and external API identity in list/detail views without overloading the list view.
- `team_elo_ratings` is now registered as a read-only SQLAdmin view so ELO history can be inspected during production support and diploma demonstration.
- `users` remains restricted: password hashes are not exposed, user deletion is disabled, and only role editing is enabled.
- Prediction, football domain, model metadata, metrics, odds, and reference data remain read-only unless explicitly reviewed later.
- Detail views are intentionally more complete than list views where tables can be wide or operationally dense.
- SQLAdmin renders UTC-naive `DateTime` fields as Moscow time using `DD.MM.YYYY HH:mm МСК`. This applies to `created_at`, `query_date`, `match_date`, `trained_at`, `collected_at`, `last_synced_at`, and `last_history_viewed_at` wherever they appear in SQLAdmin list/detail/dashboard views.
- SQLAdmin renders `Date` fields as `DD.MM.YYYY` without time. This applies to `rating_date`, `start_date`, and `end_date`.

## Defense Demo Mode

The `/admin/login` page includes a passwordless defense demo mode when `PREDICTION_FOOTBALL_ADMIN_DEMO_ENABLED=true`.

Demo access is implemented as a signed SQLAdmin session flag. It does not create a database user, does not store a demo password, and does not use Android JWT authentication.

Demo-visible views:

- `users`
- `matches`
- `match_results`
- `predictions`
- `user_query_history`
- `models`
- `model_metrics`
- `countries`
- `leagues`
- `seasons`
- `teams`

Hidden from demo sessions:

- `user_roles`
- `odds`
- `prediction_characteristic_values`
- `team_elo_ratings`
- `metrics`
- `model_types`
- `match_sources`
- `external_sources`
- `bookmakers`
- `prediction_characteristics`
- `match_statuses`

Demo sessions are read-only at both UI and route levels. Create, edit, delete, export, and custom action routes are blocked for demo sessions, including the Users role-edit form.
