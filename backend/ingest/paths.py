"""Maps each ingest category to the export file(s) it's read from.

Each entry names a `category` (the CLI --categories filter, and the
IngestDatabaseManager upsert method group), a `subtype` (the specific file
shape within that category - some categories cover several distinct JSON
shapes that each need their own parser function), and a glob pattern for
matching files relative to the export root directory.
"""

SOURCES = [
    {
        "category": "activities",
        "subtype": "activities",
        "glob": "DI_CONNECT/DI-Connect-Fitness/*summarizedActivities.json",
    },
    {
        "category": "daily_summary",
        "subtype": "daily_summary",
        "glob": "DI_CONNECT/DI-Connect-Aggregator/UDSFile_*.json",
    },
    {
        "category": "hydration",
        "subtype": "hydration",
        "glob": "DI_CONNECT/DI-Connect-Aggregator/HydrationLogFile_*.json",
    },
    {
        "category": "sleep",
        "subtype": "sleep",
        "glob": "DI_CONNECT/DI-Connect-Wellness/*_sleepData.json",
    },
    {
        "category": "biometrics",
        "subtype": "heart_rate_zones",
        "glob": "DI_CONNECT/DI-Connect-Wellness/*_heartRateZones.json",
    },
    {
        "category": "biometrics",
        "subtype": "power_zones",
        "glob": "DI_CONNECT/DI-Connect-Wellness/*_powerZones.json",
    },
    {
        "category": "biometrics",
        "subtype": "user_bio_metric_profile_data",
        "glob": "DI_CONNECT/DI-Connect-Wellness/*_userBioMetricProfileData.json",
    },
    {
        "category": "biometrics",
        "subtype": "bio_metrics_latest",
        "glob": "DI_CONNECT/DI-Connect-Wellness/*_bioMetrics_latest.json",
    },
    {
        "category": "biometrics",
        "subtype": "user_bio_metrics_history",
        "glob": "DI_CONNECT/DI-Connect-Wellness/*_userBioMetrics.json",
    },
    {
        "category": "biometrics",
        "subtype": "fitness_age_data",
        "glob": "DI_CONNECT/DI-Connect-Wellness/*_fitnessAgeData.json",
    },
    {
        "category": "training_metrics",
        "subtype": "activity_vo2_max",
        "glob": "DI_CONNECT/DI-Connect-Metrics/ActivityVo2Max_*.json",
    },
    {
        "category": "training_metrics",
        "subtype": "acute_training_load",
        "glob": "DI_CONNECT/DI-Connect-Metrics/MetricsAcuteTrainingLoad_*.json",
    },
    {
        "category": "training_metrics",
        "subtype": "max_met_data",
        "glob": "DI_CONNECT/DI-Connect-Metrics/MetricsMaxMetData_*.json",
    },
    {
        "category": "training_metrics",
        "subtype": "race_predictions",
        "glob": "DI_CONNECT/DI-Connect-Metrics/RunRacePredictions_*.json",
    },
    {
        "category": "training_metrics",
        "subtype": "training_status_history",
        "glob": "DI_CONNECT/DI-Connect-Metrics/TrainingHistory_*.json",
    },
    {
        "category": "personal_records",
        "subtype": "personal_records",
        "glob": "DI_CONNECT/DI-Connect-Fitness/*_personalRecord.json",
    },
    {
        "category": "gear",
        "subtype": "gear",
        "glob": "DI_CONNECT/DI-Connect-Fitness/*_gear.json",
    },
]

ALL_CATEGORIES = sorted({s["category"] for s in SOURCES})


def sources_for(categories):
    """Yield SOURCES entries whose category is in `categories`."""
    wanted = set(categories)
    for source in SOURCES:
        if source["category"] in wanted:
            yield source
