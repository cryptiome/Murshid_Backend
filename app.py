import os
from flask import Flask, jsonify
from flask_cors import CORS

from routes.health_routes import health_bp
from routes.test_routes import test_bp
from routes.student_plan_routes import student_plan_bp
from routes.chat_routes import chat_bp
from routes.chat_test_routes import chat_test_bp
from routes.knowledge_base_routes import knowledge_base_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({"message": "Murshid Study Plan Agent API is running"})

    app.register_blueprint(health_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(student_plan_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(chat_test_bp)
    app.register_blueprint(knowledge_base_bp)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)