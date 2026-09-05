#include "db.hpp"

#include <algorithm>

namespace activity_graph {

Database::Database(const std::string& connection_string) : conn_(connection_string) {}

std::vector<TimeSeriesPoint> Database::fetch_timeseries(const MetricDef& metric,
                                                          const std::optional<std::string>& activity_type,
                                                          const std::optional<std::string>& since, int limit) {
    const std::string column(metric.column);

    std::string sql = "SELECT a.start_time_gmt, a." + column + " FROM activities a";
    if (activity_type) {
        sql += " JOIN activity_types t ON a.activity_type_id = t.id";
    }
    sql += " WHERE a." + column + " IS NOT NULL AND a.start_time_gmt IS NOT NULL";

    pqxx::params params;
    int idx = 1;
    if (activity_type) {
        sql += " AND t.type_key = $" + std::to_string(idx++);
        params.append(*activity_type);
    }
    if (since) {
        sql += " AND a.start_time_gmt >= $" + std::to_string(idx++);
        params.append(*since);
    }
    sql += " ORDER BY a.start_time_gmt DESC LIMIT $" + std::to_string(idx++);
    params.append(limit);

    pqxx::nontransaction tx(conn_);
    pqxx::result res = tx.exec(sql, params);

    std::vector<TimeSeriesPoint> points;
    points.reserve(res.size());
    for (const auto& row : res) {
        points.push_back({row[0].as<std::string>(), row[1].as<double>() / metric.divisor});
    }
    std::reverse(points.begin(), points.end());
    return points;
}

std::vector<BarGroup> Database::fetch_aggregate(const MetricDef& metric, GroupBy group_by, Agg agg,
                                                 const std::optional<std::string>& since) {
    const std::string column(metric.column);

    std::string group_expr = (group_by == GroupBy::kType) ? "t.type_key"
                                                            : "to_char(date_trunc('month', a.start_time_gmt), 'YYYY-MM')";

    std::string sql = "SELECT " + group_expr +
                       " AS grp, COUNT(*) AS cnt, AVG(a." + column + ") AS avg_v, SUM(a." + column +
                       ") AS sum_v FROM activities a JOIN activity_types t ON a.activity_type_id = t.id"
                       " WHERE a." + column + " IS NOT NULL";

    pqxx::params params;
    int idx = 1;
    if (since) {
        sql += " AND a.start_time_gmt >= $" + std::to_string(idx++);
        params.append(*since);
    }
    sql += " GROUP BY " + group_expr + " ORDER BY " + group_expr;

    pqxx::nontransaction tx(conn_);
    pqxx::result res = tx.exec(sql, params);

    std::vector<BarGroup> groups;
    groups.reserve(res.size());
    for (const auto& row : res) {
        double value = 0.0;
        switch (agg) {
            case Agg::kCount:
                // A row count, not a physical quantity - never scaled by the metric's divisor.
                value = row["cnt"].as<double>();
                break;
            case Agg::kSum:
                value = row["sum_v"].as<double>() / metric.divisor;
                break;
            case Agg::kAvg:
                value = row["avg_v"].as<double>() / metric.divisor;
                break;
        }
        groups.push_back({row["grp"].as<std::string>(), value});
    }
    return groups;
}

}  // namespace activity_graph
