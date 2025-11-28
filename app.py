from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from models import db, Tour, User, Booking, Payment, TripSchedule, Reminder
from routes import tours_bp, auth_bp, bookings_bp, payments_bp, trip_schedules_bp, trip_scheduler_bp
from services.notifications import notification_service, mail
from data.tours_data import DEFAULT_TOURS
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

# Static files directory for frontend
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')

# CORS configuration - can be disabled when frontend is served from same origin
enable_cors = os.getenv('ENABLE_CORS', 'true').lower() == 'true'

if enable_cors:
    # Allow CORS from frontend - support multiple origins for development and production
    frontend_urls = os.getenv('FRONTEND_URL', 'http://localhost:5173').split(',')
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://twende-tours.netlify.app",
        "https://twende-frontend.onrender.com"
    ] + [url.strip() for url in frontend_urls if url.strip()]

    # Configure CORS with specific settings for all routes
    CORS(app, origins=list(set(allowed_origins)),
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         expose_headers=["Content-Type", "Authorization"])
    logger.info("CORS enabled for external frontend origins")
else:
    logger.info("CORS disabled - frontend served from same origin")

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

# Email configuration for notifications
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "noreply@twendetours.com")

db.init_app(app)

# Initialize notification service
notification_service.init_app(app)

# Register all blueprints
app.register_blueprint(tours_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(trip_schedules_bp)
app.register_blueprint(trip_scheduler_bp)

@app.route("/")
def root():
    """Serve frontend index.html if it exists, otherwise return API info"""
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    return jsonify({
        "message": "Twende Tours API running",
        "version": "1.0.0",
        "endpoints": {
            "tours": "/api/tours",
            "auth": "/api/auth",
            "bookings": "/api/bookings",
            "payments": "/api/payments",
            "trip_schedules": "/api/trip-schedules",
            "trip_scheduler": "/api/trip-scheduler",
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


@app.errorhandler(404)
def not_found(e):
    """Serve frontend index.html for SPA routing on non-API routes"""
    # Don't serve frontend for API routes - return 404 JSON
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404

    # Check if frontend index.html exists
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_FOLDER, 'index.html')

    # No frontend deployed, return API info
    return jsonify({
        'error': 'Not found',
        'message': 'Frontend not deployed. API endpoints are available at /api/*'
    }), 404

with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created/verified successfully")
        
        # Auto-seed tours if enabled and no tours exist
        auto_seed = os.getenv('AUTO_SEED_TOURS', 'true').lower() == 'true'
        if auto_seed:
            tour_count = Tour.query.count()
            if tour_count == 0:
                logger.info("No tours found in database. Auto-seeding default tours...")
                created_count = 0
                for tour_data in DEFAULT_TOURS:
                    try:
                        new_tour = Tour(**tour_data)
                        db.session.add(new_tour)
                        created_count += 1
                    except Exception as tour_error:
                        # Expunge any invalid object from the session
                        db.session.rollback()
                        logger.warning(f"Failed to create tour '{tour_data.get('title', 'unknown')}': {str(tour_error)}")
                try:
                    db.session.commit()
                    logger.info(f"Auto-seeded {created_count} tours successfully")
                except Exception as commit_error:
                    db.session.rollback()
                    logger.error(f"Failed to commit auto-seeded tours: {str(commit_error)}")
            else:
                logger.info(f"Database already contains {tour_count} tours. Skipping auto-seed.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    logger.info(f"Starting Twende Tours API on port {port} (debug={debug})")
    app.run(debug=debug, port=port, host="0.0.0.0")