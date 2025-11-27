from flask import Flask, jsonify
from flask_cors import CORS
from models import db, Tour, User, Booking, Payment
from routes import tours_bp, auth_bp, bookings_bp, payments_bp
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
log_level = logging.DEBUG if os.getenv('FLASK_ENV') == 'development' else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Allow CORS from frontend - support multiple origins for development and production
frontend_urls = os.getenv('FRONTEND_URL', 'http://localhost:5173').split(',')
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://twende-tours.netlify.app",
    "https://twende-frontend.onrender.com"
] + [url.strip() for url in frontend_urls if url.strip()]

CORS(app, origins=list(set(allowed_origins)), supports_credentials=True)

# Database configuration with connection pool settings
database_url = os.getenv("DATABASE_URL", "postgresql://localhost/twende_tours")
# Handle Railway's postgres:// to postgresql:// conversion
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

logger.info(f"Database URL configured (connection details hidden)")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

db.init_app(app)

# Register all blueprints
app.register_blueprint(tours_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(payments_bp)

@app.route("/")
def root():
    return jsonify({
        "message": "Twende Tours API running",
        "version": "1.0.0",
        "endpoints": {
            "tours": "/api/tours",
            "auth": "/api/auth",
            "bookings": "/api/bookings",
            "payments": "/api/payments",
            "health": "/health"
        }
    })

@app.route("/health")
def health():
    """Health check endpoint with database status"""
    db_status = "healthy"
    try:
        # Test database connection
        db.session.execute(db.text("SELECT 1"))
        db.session.commit()
        logger.debug("Health check: Database connection successful")
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Health check: Database connection failed - {str(e)}")

    return jsonify({
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "service": "twende-backend"
    })

with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    logger.info(f"Starting Twende Tours API on port {port} (debug={debug})")
    app.run(debug=debug, port=port, host="0.0.0.0")