#pragma once

#include <array>
#include <optional>
#include <string_view>

namespace activity_graph {

struct MetricDef {
    std::string_view key;     // CLI-facing name, e.g. "distance"
    std::string_view column;  // real activities column name, e.g. "distance_meters"
    std::string_view label;   // human-readable label with unit, e.g. "Distance (km)"
    double divisor = 1.0;     // raw column value is divided by this before display
};

// Curated, deliberately small set of metrics an end user would actually want
// to see - not an attempt to expose all ~85 columns on `activities`.
inline constexpr std::array<MetricDef, 8> kMetrics{{
    {"distance", "distance_meters", "Distance (km)", 1000.0},
    {"duration", "duration_seconds", "Duration (s)"},
    {"speed", "avg_speed_mps", "Avg Speed (m/s)"},
    {"heart-rate", "avg_hr", "Avg Heart Rate (bpm)"},
    {"calories", "calories", "Calories (kcal)"},
    {"steps", "steps", "Steps"},
    {"elevation-gain", "elevation_gain_meters", "Elevation Gain (m)"},
    {"vo2max", "vo2_max_value", "VO2 Max"},
}};

inline std::optional<MetricDef> find_metric(std::string_view key) {
    for (const auto& m : kMetrics) {
        if (m.key == key) {
            return m;
        }
    }
    return std::nullopt;
}

}  // namespace activity_graph
