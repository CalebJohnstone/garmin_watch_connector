#include <algorithm>
#include <iostream>
#include <optional>

#include <CLI/CLI.hpp>
#include <ftxui/dom/node.hpp>
#include <ftxui/screen/screen.hpp>
#include <ftxui/screen/terminal.hpp>

#include "charts.hpp"
#include "db.hpp"
#include "env_config.hpp"
#include "metrics.hpp"

using namespace activity_graph;

namespace {

void print_metrics() {
    std::cout << "Available metrics:\n";
    for (const auto& m : kMetrics) {
        std::cout << "  " << m.key << "\t" << m.label << "\n";
    }
}

std::optional<std::string> to_optional(const std::string& s) {
    return s.empty() ? std::nullopt : std::make_optional(s);
}

}  // namespace

int main(int argc, char** argv) {
    CLI::App app{"Render line/bar charts of Garmin activities data in the terminal"};

    bool list_metrics = false;
    app.add_flag("--list-metrics", list_metrics, "List available --metric values and exit");

    std::string chart_type;
    app.add_option("-t,--type", chart_type, "Chart type: line or bar")->check(CLI::IsMember({"line", "bar"}));

    std::string metric_key;
    app.add_option("-m,--metric", metric_key, "Metric to plot (see --list-metrics)");

    std::string activity_type;
    app.add_option("--activity-type", activity_type, "Filter to one activity type (e.g. running)");

    std::string since;
    app.add_option("--since", since, "Only include activities on/after this date (YYYY-MM-DD)");

    int limit = 200;
    app.add_option("--limit", limit, "Max number of most-recent activities to plot (line chart)");

    std::string group_by = "type";
    app.add_option("--group-by", group_by, "Bar chart grouping: type or month")
        ->check(CLI::IsMember({"type", "month"}));

    std::string agg = "count";
    app.add_option("--agg", agg, "Bar chart aggregation: count, sum, or avg")
        ->check(CLI::IsMember({"count", "sum", "avg"}));

    int width = 0;
    app.add_option("--width", width, "Chart width in terminal columns (default: terminal width)");
    int height = 0;
    app.add_option("--height", height, "Chart height in terminal rows (default: terminal height, minus margin)");

    CLI11_PARSE(app, argc, argv);

    if (list_metrics) {
        print_metrics();
        return 0;
    }

    if (chart_type.empty()) {
        std::cerr << "Error: --type is required (line or bar). Run --help for usage.\n";
        return 1;
    }

    const auto metric = find_metric(metric_key);
    if (!metric) {
        std::cerr << "Error: unknown --metric '" << metric_key << "'.\n";
        print_metrics();
        return 1;
    }

    const auto term_size = ftxui::Terminal::Size();
    if (width <= 0) {
        width = std::max(20, term_size.dimx - 2);
    }
    if (height <= 0) {
        height = std::max(10, term_size.dimy - 8);
    }

    try {
        const EnvConfig env = load_env_config();
        Database db(env.connection_string());

        const auto activity_type_opt = to_optional(activity_type);
        const auto since_opt = to_optional(since);

        ftxui::Element root;
        if (chart_type == "line") {
            const auto points = db.fetch_timeseries(*metric, activity_type_opt, since_opt, limit);
            root = make_line_chart(points, *metric, width, height);
        } else {
            const GroupBy group = (group_by == "month") ? GroupBy::kMonth : GroupBy::kType;
            const Agg aggregation = (agg == "sum") ? Agg::kSum : (agg == "avg" ? Agg::kAvg : Agg::kCount);
            const auto groups = db.fetch_aggregate(*metric, group, aggregation, since_opt);
            root = make_bar_chart(groups, *metric, width, height);
        }

        auto screen = ftxui::Screen::Create(ftxui::Dimension::Fixed(width), ftxui::Dimension::Fixed(height + 4));
        ftxui::Render(screen, root);
        std::cout << screen.ToString() << "\n";
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
