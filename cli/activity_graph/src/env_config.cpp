#include "env_config.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <optional>
#include <sstream>

namespace activity_graph {

namespace {

namespace fs = std::filesystem;

std::optional<std::string> get_env(const char* name) {
    if (const char* value = std::getenv(name)) {
        return std::string(value);
    }
    return std::nullopt;
}

std::string trim(const std::string& s) {
    const auto begin = s.find_first_not_of(" \t\r\n");
    if (begin == std::string::npos) {
        return "";
    }
    const auto end = s.find_last_not_of(" \t\r\n");
    return s.substr(begin, end - begin + 1);
}

std::string strip_quotes(std::string s) {
    if (s.size() >= 2 && ((s.front() == '"' && s.back() == '"') || (s.front() == '\'' && s.back() == '\''))) {
        return s.substr(1, s.size() - 2);
    }
    return s;
}

// Finds a `.env` file by walking up from the current working directory,
// since this binary won't always be invoked from the repo root.
std::optional<fs::path> find_dotenv() {
    fs::path dir = fs::current_path();
    for (int i = 0; i < 16; ++i) {
        fs::path candidate = dir / ".env";
        if (fs::exists(candidate)) {
            return candidate;
        }
        if (!dir.has_parent_path() || dir == dir.parent_path()) {
            break;
        }
        dir = dir.parent_path();
    }
    return std::nullopt;
}

// Deliberately simple: KEY=VALUE lines, skip blanks/#-comments, strip
// optional surrounding quotes. No multiline values, no interpolation - the
// real .env file here is 7 flat lines, no need for full dotenv semantics.
std::map<std::string, std::string> parse_dotenv(const fs::path& path) {
    std::map<std::string, std::string> values;
    std::ifstream file(path);
    std::string line;
    while (std::getline(file, line)) {
        const std::string trimmed = trim(line);
        if (trimmed.empty() || trimmed[0] == '#') {
            continue;
        }
        const auto eq = trimmed.find('=');
        if (eq == std::string::npos) {
            continue;
        }
        std::string key = trim(trimmed.substr(0, eq));
        std::string value = strip_quotes(trim(trimmed.substr(eq + 1)));
        values[key] = value;
    }
    return values;
}

std::string resolve(const char* env_name, const std::map<std::string, std::string>& dotenv,
                     const std::string& fallback) {
    if (auto value = get_env(env_name)) {
        return *value;
    }
    if (auto it = dotenv.find(env_name); it != dotenv.end()) {
        return it->second;
    }
    return fallback;
}

// Quotes a libpq connection-string value: wrapped in single quotes, with
// embedded backslashes and single quotes backslash-escaped, per PostgreSQL's
// conninfo format - necessary since passwords may contain arbitrary characters.
std::string quote_conninfo_value(const std::string& value) {
    std::string quoted = "'";
    for (char c : value) {
        if (c == '\\' || c == '\'') {
            quoted += '\\';
        }
        quoted += c;
    }
    quoted += "'";
    return quoted;
}

}  // namespace

std::string EnvConfig::connection_string() const {
    std::ostringstream out;
    out << "host=" << quote_conninfo_value(host) << " port=" << quote_conninfo_value(port)
        << " dbname=" << quote_conninfo_value(dbname) << " user=" << quote_conninfo_value(user)
        << " password=" << quote_conninfo_value(password);
    return out.str();
}

EnvConfig load_env_config() {
    std::map<std::string, std::string> dotenv;
    if (auto path = find_dotenv()) {
        dotenv = parse_dotenv(*path);
    }

    EnvConfig config;
    config.host = resolve("DB_HOST", dotenv, "localhost");
    config.dbname = resolve("DB_NAME", dotenv, "garmin_data");
    config.user = resolve("DB_USER", dotenv, "postgres");
    config.password = resolve("DB_PASSWORD", dotenv, "");
    config.port = resolve("DB_PORT", dotenv, "5432");
    return config;
}

}  // namespace activity_graph
