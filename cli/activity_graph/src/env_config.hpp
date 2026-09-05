#pragma once

#include <string>

namespace activity_graph {

struct EnvConfig {
    std::string host = "localhost";
    std::string dbname = "garmin_data";
    std::string user = "postgres";
    std::string password;
    std::string port = "5432";

    std::string connection_string() const;
};

// Mirrors config.py: real environment variables (DB_HOST/DB_NAME/DB_USER/
// DB_PASSWORD/DB_PORT) take precedence; otherwise falls back to a `.env`
// file found by walking up from the current working directory.
EnvConfig load_env_config();

}  // namespace activity_graph
