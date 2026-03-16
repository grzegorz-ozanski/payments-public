"""
    Main mock application
"""
from pathlib import Path

from flask import Flask, Response, request

from mockserver.providers import actum_bp, energa_bp, multimedia_bp, nordhome_bp, opec_bp, pgnig_bp, pewik_bp, vectra_bp

LOG_FILE = Path('log.txt')


def create_app() -> Flask:
    """
    Creates main mock Flask application
    :return: Mock application
    """
    flask_app = Flask(__name__)

    LOG_FILE.unlink(missing_ok=True)

    @flask_app.before_request
    def log_request() -> None:
        """Print each incoming request to help debug mock-server routing."""
        message = f"{request.method} {request.url}"
        print(message)
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f'{message}\n')

    @flask_app.get("/content/InetObsKontr/<path:_asset_path>")
    def content_asset(_asset_path: str) -> Response:
        """Return a tiny placeholder payload for shared archived IOK asset URLs."""
        if _asset_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
            return Response(b"", mimetype="image/png")
        if _asset_path.endswith((".css", ".js", ".json", ".map", ".webmanifest")):
            return Response("", mimetype="text/plain")
        return Response("", mimetype="application/octet-stream")

    flask_app.register_blueprint(actum_bp)
    flask_app.register_blueprint(energa_bp)
    flask_app.register_blueprint(multimedia_bp)
    flask_app.register_blueprint(nordhome_bp)
    flask_app.register_blueprint(opec_bp)
    flask_app.register_blueprint(pgnig_bp)
    flask_app.register_blueprint(pewik_bp)
    flask_app.register_blueprint(vectra_bp)
    return flask_app


app = create_app()

def main() -> None:
    """Run the local mock server."""
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    main()
