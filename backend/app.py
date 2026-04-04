import sys
import os

# Add parent directory to path so we can import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_cors import CORS
from routes.activities import activities_bp
from routes.steps import steps_bp

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
CORS(app)

app.register_blueprint(activities_bp, url_prefix="/api/activities")
app.register_blueprint(steps_bp, url_prefix="/api/steps")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve the Rust/WASM frontend"""
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
