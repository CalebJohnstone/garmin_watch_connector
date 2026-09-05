#pragma once

#include <optional>
#include <string>
#include <vector>

#include <pqxx/pqxx>

#include "metrics.hpp"

namespace activity_graph {

struct TimeSeriesPoint {
    std::string timestamp;  // raw text form of start_time_gmt, e.g. "2024-02-19 22:00:00"
    double value = 0.0;
};

enum class GroupBy { kType, kMonth };
enum class Agg { kCount, kSum, kAvg };

struct BarGroup {
    std::string label;
    double value = 0.0;
};

class Database {
public:
    explicit Database(const std::string& connection_string);

    // One row per activity, chronological ascending, matching `metric` IS NOT
    // NULL. `activity_type`/`since` are optional filters; `limit` caps how
    // many of the most recent matching activities are returned.
    std::vector<TimeSeriesPoint> fetch_timeseries(const MetricDef& metric,
                                                   const std::optional<std::string>& activity_type,
                                                   const std::optional<std::string>& since, int limit);

    // One row per group (activity type, or calendar month), aggregated per
    // `agg`. `since` is an optional lower bound on start_time_gmt.
    std::vector<BarGroup> fetch_aggregate(const MetricDef& metric, GroupBy group_by, Agg agg,
                                           const std::optional<std::string>& since);

private:
    pqxx::connection conn_;
};

}  // namespace activity_graph
