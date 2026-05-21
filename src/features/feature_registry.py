BASE_FEATURES = [
    "Division",
    "HomeTeam",
    "AwayTeam",
    "SeasonStartYear",
    "MatchMonth",
]

ELO_FEATURES = [
    "HomeElo",
    "AwayElo",
    "HomeEloSynced",
    "AwayEloSynced",
    "EloDiff",
    "EloMean",
]

ODDS_FEATURES = [
    "OddHome",
    "OddDraw",
    "OddAway",
    "Over25",
    "Under25",
    "ImpliedHomeWin",
    "ImpliedDraw",
    "ImpliedAwayWin",
    "ImpliedOver25",
    "ImpliedUnder25",
    "BookmakerMargin1X2",
]

ROLLING_V1_FEATURES = [
    "HomeMatchesPlayedBefore",
    "AwayMatchesPlayedBefore",
    "HomeRollingGoalsFor5",
    "HomeRollingGoalsAgainst5",
    "AwayRollingGoalsFor5",
    "AwayRollingGoalsAgainst5",
    "HomeRollingPoints3",
    "HomeRollingPoints5",
    "AwayRollingPoints3",
    "AwayRollingPoints5",
    "RollingGoalsForDiff5",
    "RollingGoalsAgainstDiff5",
    "RollingPointsDiff3",
    "RollingPointsDiff5",
]

V1_FEATURES = BASE_FEATURES + ELO_FEATURES + ODDS_FEATURES + ROLLING_V1_FEATURES

ROLLING_V2_BTTS_OVER_FEATURES = [
    "HomeRollingBTTSRate5",
    "AwayRollingBTTSRate5",
    "RollingBTTSRateDiff5",
    "HomeRollingOver25Rate5",
    "AwayRollingOver25Rate5",
    "RollingOver25RateDiff5",
]

ROLLING_V2_CORNERS_YELLOW_FEATURES = [
    "HomeRollingCornersFor5",
    "HomeRollingCornersAgainst5",
    "AwayRollingCornersFor5",
    "AwayRollingCornersAgainst5",
    "RollingCornersForDiff5",
    "RollingCornersAgainstDiff5",
    "HomeRollingYellowCardsFor5",
    "HomeRollingYellowCardsAgainst5",
    "AwayRollingYellowCardsFor5",
    "AwayRollingYellowCardsAgainst5",
    "RollingYellowCardsForDiff5",
    "RollingYellowCardsAgainstDiff5",
]

ROLLING_V2_VENUE_FORM_FEATURES = [
    "HomeOnlyRollingPoints5",
    "HomeOnlyRollingGoalsFor5",
    "HomeOnlyRollingGoalsAgainst5",
    "AwayOnlyRollingPoints5",
    "AwayOnlyRollingGoalsFor5",
    "AwayOnlyRollingGoalsAgainst5",
    "VenueRollingPointsDiff5",
    "VenueRollingGoalsForDiff5",
    "VenueRollingGoalsAgainstDiff5",
]

ROLLING_V2_FEATURES = (
    ROLLING_V2_BTTS_OVER_FEATURES
    + ROLLING_V2_CORNERS_YELLOW_FEATURES
    + ROLLING_V2_VENUE_FORM_FEATURES
)

V2_FEATURES = V1_FEATURES + ROLLING_V2_FEATURES

OUTCOME_FEATURE_SETS = {
    "v1_only": V1_FEATURES,
    "v1_btts_over": V1_FEATURES + ROLLING_V2_BTTS_OVER_FEATURES,
    "v1_corners_yellow": V1_FEATURES + ROLLING_V2_CORNERS_YELLOW_FEATURES,
    "full_v2": V2_FEATURES,
}

BTTS_RELATED_ROLLING_FEATURES = ROLLING_V2_BTTS_OVER_FEATURES

BTTS_FEATURE_SETS = {
    "v1_only": V1_FEATURES,
    "v1_btts_related": V1_FEATURES + BTTS_RELATED_ROLLING_FEATURES,
}

OVER25_RELATED_ROLLING_FEATURES = ROLLING_V2_BTTS_OVER_FEATURES

OVER25_FEATURE_SETS = {
    "v1_only": V1_FEATURES,
    "v1_over25_related": V1_FEATURES + OVER25_RELATED_ROLLING_FEATURES,
}

TARGET_COLUMNS = [
    "Target_Outcome",
    "Target_BTTS",
    "Target_Over25",
    "Target_Corners_Over95",
    "Target_YellowCards_Over35",
    "Target_HomeGoals",
    "Target_AwayGoals",
]

LEAKAGE_COLUMNS = [
    "FTHome",
    "FTAway",
    "FTResult",
    "HTHome",
    "HTAway",
    "HTResult",
    "HomeShots",
    "AwayShots",
    "HomeTarget",
    "AwayTarget",
    "HomeFouls",
    "AwayFouls",
    "HomeCorners",
    "AwayCorners",
    "HomeYellow",
    "AwayYellow",
    "HomeRed",
    "AwayRed",
]
