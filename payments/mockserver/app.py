from flask import Flask

from payments.mockserver.providers import actum_bp, nordhome_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(actum_bp)
    app.register_blueprint(nordhome_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)