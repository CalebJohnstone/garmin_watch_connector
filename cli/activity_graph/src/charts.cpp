#include "charts.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <format>

using namespace ftxui;

namespace activity_graph {

namespace {

std::string format_value(double value) {
    return std::format("{:.1f}", value);
}

}  // namespace

Element make_line_chart(const std::vector<TimeSeriesPoint>& points, const MetricDef& metric, int cols, int rows) {
    const std::string title = std::string(metric.label) + " - last " + std::to_string(points.size()) + " activities";

    if (points.empty()) {
        return vbox({
            text(title) | bold,
            text("No data for this metric/filter combination."),
        });
    }

    double min_v = points.front().value;
    double max_v = points.front().value;
    for (const auto& p : points) {
        min_v = std::min(min_v, p.value);
        max_v = std::max(max_v, p.value);
    }
    if (max_v - min_v < 1e-9) {
        max_v = min_v + 1.0;
    }

    // Captured by value: `canvas()` stores this lambda inside the returned
    // Element and invokes it later during Render(), well after this
    // function's stack frame (and any by-reference captures of its locals)
    // would otherwise be gone.
    auto draw = [points, min_v, max_v](Canvas& c) {
        const int w = c.width();
        const int h = c.height();

        auto point_xy = [&](std::size_t i) -> std::pair<int, int> {
            const int x = (points.size() == 1)
                              ? 0
                              : static_cast<int>(static_cast<double>(i) / static_cast<double>(points.size() - 1) *
                                                  (w - 1));
            const double norm = (points[i].value - min_v) / (max_v - min_v);
            const int y = h - 1 - static_cast<int>(norm * (h - 1));
            return {x, y};
        };

        if (points.size() == 1) {
            const auto [x, y] = point_xy(0);
            c.DrawPointCircleFilled(x, y, 1, Color::BlueLight);
        } else {
            for (std::size_t i = 1; i < points.size(); ++i) {
                const auto [x1, y1] = point_xy(i - 1);
                const auto [x2, y2] = point_xy(i);
                c.DrawPointLine(x1, y1, x2, y2, Color::BlueLight);
            }
        }

        c.DrawText(0, 0, format_value(max_v), Color::GrayLight);
        c.DrawText(0, h - 4, format_value(min_v), Color::GrayLight);
    };

    auto canvas_element = canvas(cols * 2, rows * 4, draw) | size(WIDTH, EQUAL, cols) | size(HEIGHT, EQUAL, rows);

    return vbox({
        text(title) | bold,
        canvas_element | border,
        hbox({text(points.front().timestamp), filler(), text(points.back().timestamp)}),
    });
}

Element make_bar_chart(const std::vector<BarGroup>& groups, const MetricDef& metric, int cols) {
    const std::string title = std::string(metric.label) + " - by group";

    if (groups.empty()) {
        return vbox({
            text(title) | bold,
            text("No data for this metric/filter combination."),
        });
    }

    double max_v = 0.0;
    for (const auto& g : groups) {
        max_v = std::max(max_v, g.value);
    }
    if (max_v <= 0.0) {
        max_v = 1.0;
    }

    static const std::array<Color, 4> kPalette{Color::BlueLight, Color::GreenLight, Color::YellowLight,
                                                Color::RedLight};

    Elements rows_el;
    for (std::size_t i = 0; i < groups.size(); ++i) {
        const auto& group = groups[i];
        const float progress = static_cast<float>(std::clamp(group.value / max_v, 0.0, 1.0));
        rows_el.push_back(hbox({
            text(group.label) | size(WIDTH, EQUAL, 20),
            text(" "),
            gauge(progress) | color(kPalette[i % kPalette.size()]) | flex,
            text(" " + format_value(group.value)),
        }));
    }

    // No height constraint here - a bar chart always shows every group
    // (e.g. every month in range), even if that's taller than one screen.
    return vbox({
               text(title) | bold,
               separator(),
               vbox(rows_el),
           }) |
           size(WIDTH, EQUAL, cols);
}

}  // namespace activity_graph
