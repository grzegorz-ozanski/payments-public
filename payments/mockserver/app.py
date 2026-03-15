"""
    Main mock application
"""
from flask import Flask

from payments.mockserver.providers import actum_bp, nordhome_bp, pewik_bp


def create_app() -> Flask:
    """
    Creates main mock Flask application
    :return: Mock application
    """
    flask_app = Flask(__name__)
    flask_app.register_blueprint(actum_bp)
    flask_app.register_blueprint(nordhome_bp)
    flask_app.register_blueprint(pewik_bp)
    return flask_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
