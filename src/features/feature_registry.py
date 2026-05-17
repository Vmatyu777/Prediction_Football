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
