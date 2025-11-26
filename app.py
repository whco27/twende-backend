from flask import Flask, jsonify
from flask_cors import CORS
from models.tour import db, Tour
from routes import tours_bp
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Allow CORS from frontend
CORS(app, origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "https://twende-tours.netlify.app",
    "https://twende-frontend.onrender.com"
])

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://postgres:173@localhost:5432/twende_tours")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
app.register_blueprint(tours_bp)

@app.route("/")
def root():
    return jsonify({"message": "Twende Tours API running"})

@app. route("/health")
def health():
    return jsonify({"status": "healthy"})

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="127.0.0.1")