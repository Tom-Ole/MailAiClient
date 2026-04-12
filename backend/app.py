import os
from flask import Flask, jsonify
from flask_session import Session

from config import Config
from util.connections import teardown_connections
from routes import auth, mail, folders, compose, ai


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    Session(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(mail.bp)
    app.register_blueprint(folders.bp)
    app.register_blueprint(compose.bp)
    app.register_blueprint(ai.bp)


    app.teardown_appcontext(teardown_connections)


    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": str(e.desciption)}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": str(e.description)}), 401
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)