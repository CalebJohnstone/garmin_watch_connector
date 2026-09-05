#pragma once

#include <ftxui/dom/elements.hpp>

#include "db.hpp"
#include "metrics.hpp"

namespace activity_graph {

// A Canvas-drawn line chart of `points` in chronological order.
ftxui::Element make_line_chart(const std::vector<TimeSeriesPoint>& points, const MetricDef& metric, int cols,
                                int rows);

// A horizontal-bar chart (one row per group) of `groups`. Always renders
// every group - no height cap, since a "-print and exit" tool has no
// scrolling and shouldn't silently drop data (e.g. later months).
ftxui::Element make_bar_chart(const std::vector<BarGroup>& groups, const MetricDef& metric, int cols);

}  // namespace activity_graph
