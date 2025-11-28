"""Authentication routes for user registration and login"""
from flask import Blueprint, jsonify, request
from models import db, User
from services.notifications import notification_service
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError, DataError
import re
import logging
import time

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Maximum lengths for database fields
MAX_EMAIL_LENGTH = 255
MAX_NAME_LENGTH = 100
MAX_PHONE_LENGTH = 20

# Default pagination settings
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100

# Retry configuration for transient database errors
MAX_DB_RETRIES = 3
RETRY_DELAY_SECONDS = 0.5


def sanitize_string(value):
    """Sanitize string input by stripping whitespace"""
    if value is None:
        return None
    return str(value).strip()


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength (min 8 characters)"""
    return len(password) >= 8


def validate_phone_number(phone):
    """Validate phone number format (optional, basic validation)"""
    if not phone:
        return True  # Phone is optional
    # Allow digits, spaces, dashes, plus sign, and parentheses
    pattern = r'^[\d\s\-+()]+$'
    return re.match(pattern, phone) is not None


def check_database_health():
    """Check if database connection is healthy.
    
    Returns:
        tuple: (is_healthy, error_message)
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def commit_with_retry(max_retries=MAX_DB_RETRIES, delay=RETRY_DELAY_SECONDS):
    """Attempt to commit database session with retry logic for transient errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
        
    Returns:
        tuple: (success, error_type, error_message)
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            db.session.commit()
            return True, None, None
        except OperationalError as e:
            last_error = e
            db.session.rollback()
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database operational error on commit (attempt {attempt + 1}/{max_retries}): "
                    f"{str(e)}. Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"Database operational error persisted after {max_retries} attempts: {str(e)}"
                )
                return False, 'OperationalError', str(e)
        except IntegrityError as e:
            db.session.rollback()
            return False, 'IntegrityError', str(e)
        except Exception as e:
            db.session.rollback()
            return False, type(e).__name__, str(e)
    
    return False, 'OperationalError', str(last_error) if last_error else 'Unknown error'


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json(silent=True)
        logger.info("Registration request received")

        if not data:
            logger.warning("Registration failed: No data provided")
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'message': 'Please provide registration data in JSON format',
                'required_fields': ['email', 'password', 'first_name', 'last_name'],
                'optional_fields': ['phone_number']
            }), 400

        # Sanitize inputs (strip whitespace)
        email = sanitize_string(data.get('email'))
        password = data.get('password', '')  # Don't strip password whitespace
        first_name = sanitize_string(data.get('first_name'))
        last_name = sanitize_string(data.get('last_name'))
        phone_number = sanitize_string(data.get('phone_number'))

        # Handle case where frontend sends 'name' instead of 'first_name' and 'last_name'
        if not first_name and not last_name and data.get('name'):
            name_parts = sanitize_string(data.get('name')).split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]
            logger.debug("Converted 'name' field to first_name and last_name")

        # Validate required fields
        if not email:
            logger.warning("Registration failed: Missing email")
            return jsonify({
                'success': False,
                'error': 'Missing required field: email',
                'message': 'Email address is required for registration'
            }), 400
        if not password:
            logger.warning("Registration failed: Missing password")
            return jsonify({
                'success': False,
                'error': 'Missing required field: password',
                'message': 'Password is required for registration'
            }), 400
        if not first_name:
            logger.warning("Registration failed: Missing first_name")
            return jsonify({
                'success': False,
                'error': 'Missing required field: first_name',
                'message': 'First name is required. You can also send a "name" field which will be split into first and last name.'
            }), 400
        if not last_name:
            logger.warning("Registration failed: Missing last_name")
            return jsonify({
                'success': False,
                'error': 'Missing required field: last_name',
                'message': 'Last name is required. You can also send a "name" field which will be split into first and last name.'
            }), 400

        # Validate email format
        if not validate_email(email):
            logger.warning("Registration failed: Invalid email format")
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400

        # Validate email length
        if len(email) > MAX_EMAIL_LENGTH:
            logger.warning(f"Registration failed: Email too long ({len(email)} characters)")
            return jsonify({
                'success': False,
                'error': f'Email must be {MAX_EMAIL_LENGTH} characters or less'
            }), 400

        # Validate name lengths
        if len(first_name) > MAX_NAME_LENGTH:
            logger.warning(f"Registration failed: First name too long ({len(first_name)} characters)")
            return jsonify({
                'success': False,
                'error': f'First name must be {MAX_NAME_LENGTH} characters or less'
            }), 400
        if len(last_name) > MAX_NAME_LENGTH:
            logger.warning(f"Registration failed: Last name too long ({len(last_name)} characters)")
            return jsonify({
                'success': False,
                'error': f'Last name must be {MAX_NAME_LENGTH} characters or less'
            }), 400

        # Validate phone number length if provided
        if phone_number and len(phone_number) > MAX_PHONE_LENGTH:
            logger.warning(f"Registration failed: Phone number too long ({len(phone_number)} characters)")
            return jsonify({
                'success': False,
                'error': f'Phone number must be {MAX_PHONE_LENGTH} characters or less'
            }), 400

        # Validate phone number format if provided
        if phone_number and not validate_phone_number(phone_number):
            logger.warning("Registration failed: Invalid phone number format")
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format. Only digits, spaces, dashes, plus sign, and parentheses are allowed.'
            }), 400

        # Validate password strength
        if not validate_password(password):
            logger.warning("Registration failed: Password too weak")
            return jsonify({
                'success': False,
                'error': 'Password must be at least 8 characters long'
            }), 400

        # Check if user already exists
        logger.debug("Checking for existing user with email")
        existing_user = User.query.filter_by(email=email.lower()).first()
        if existing_user:
            logger.warning("Registration failed: Email already exists")
            return jsonify({
                'success': False,
                'error': 'A user with this email already exists',
                'error_code': 'EMAIL_ALREADY_EXISTS',
                'message': 'This email address is already registered. Please use a different email or try logging in instead.',
                'suggestions': [
                    'Use a different email address',
                    'Try logging in with your existing account',
                    'Use the forgot password feature if you forgot your credentials'
                ]
            }), 409

        # Create new user
        email_domain = email.split('@')[1] if '@' in email else 'unknown'
        logger.debug(f"Creating new user for domain: {email_domain}")
        new_user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number
        )
        new_user.set_password(password)

        # Add user and commit with retry logic for transient errors
        db.session.add(new_user)
        success, error_type, error_msg = commit_with_retry()
        
        if not success:
            if error_type == 'IntegrityError':
                # Handle race condition: another request inserted the same email
                # between our check and insert
                logger.warning(
                    f"Registration failed due to duplicate email (race condition): "
                    f"{email.lower()}"
                )
                return jsonify({
                    'success': False,
                    'error': 'This email address is already registered',
                    'error_code': 'EMAIL_ALREADY_EXISTS',
                    'message': 'Please use a different email address or try logging in.',
                    'suggestions': [
                        'Use a different email address',
                        'Try logging in with your existing account'
                    ]
                }), 409
            elif error_type == 'OperationalError':
                logger.error(f"Registration failed with database connection error: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Database connection error. Please try again later.',
                    'error_code': 'DATABASE_CONNECTION_ERROR',
                    'retry': True
                }), 503
            else:
                logger.error(f"Registration failed during commit: {error_type}: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Registration failed. Please try again later.',
                    'error_code': 'COMMIT_ERROR'
                }), 500
        
        logger.info(f"User registered successfully: id={new_user.id}")

        # Send notification emails (non-blocking - failures don't affect registration)
        try:
            notification_service.send_registration_confirmation(new_user)
        except Exception as e:
            logger.warning(
                f"Failed to send registration confirmation email: {str(e)}"
            )

        try:
            notification_service.notify_admin_new_registration(new_user)
        except Exception as e:
            logger.warning(
                f"Failed to send admin notification email: {str(e)}"
            )

        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201

    except ProgrammingError as e:
        db.session.rollback()
        error_msg = str(e)
        logger.error(f"Registration failed with database programming error: {error_msg}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database tables not initialized. Please contact administrator.',
            'error_code': 'DATABASE_NOT_INITIALIZED',
            'details': 'The users table may not exist. Database migration may be required.'
        }), 500

    except OperationalError as e:
        db.session.rollback()
        error_msg = str(e)
        logger.error(f"Registration failed with database operational error: {error_msg}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database connection error. Please try again later.',
            'error_code': 'DATABASE_CONNECTION_ERROR'
        }), 500

    except DataError as e:
        db.session.rollback()
        error_msg = str(e)
        logger.error(f"Registration failed with data error: {error_msg}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Invalid data format. Please check your input values.',
            'error_code': 'DATA_FORMAT_ERROR'
        }), 400

    except Exception as e:
        db.session.rollback()
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"Registration failed with exception: {error_type}: {error_msg}", exc_info=True)
        
        return jsonify({
            'success': False,
            'error': 'Registration failed. Please try again later.',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return user info"""
    try:
        data = request.get_json(silent=True)
        logger.info("Login request received")

        if not data:
            logger.warning("Login failed: No data provided")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        if 'email' not in data or 'password' not in data:
            logger.warning("Login failed: Missing email or password")
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400

        # Find user
        user = User.query.filter_by(email=data['email'].lower()).first()

        if not user or not user.check_password(data['password']):
            logger.warning("Login failed: Invalid credentials")
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

        if not user.is_active:
            logger.warning(f"Login failed: Account deactivated for user id={user.id}")
            return jsonify({
                'success': False,
                'error': 'Account is deactivated',
                'error_code': 'ACCOUNT_DEACTIVATED',
                'message': 'Your account has been deactivated. Please contact support for assistance.'
            }), 403

        logger.info(f"User logged in successfully: id={user.id}")
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Login failed. Please try again later.'
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    try:
        logger.debug(f"Get user request: id={user_id}")
        user = db.session.get(User, user_id)
        if not user:
            logger.warning(f"Get user failed: User not found id={user_id}")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Get user failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user. Please try again later.'
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    try:
        logger.debug(f"Update user request: id={user_id}")
        user = db.session.get(User, user_id)
        if not user:
            logger.warning(f"Update user failed: User not found id={user_id}")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        data = request.get_json(silent=True)
        if not data:
            logger.warning("Update user failed: No data provided")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate name fields if provided (cannot be empty)
        name_fields = ['first_name', 'last_name']
        for field in name_fields:
            if field in data:
                value = sanitize_string(data[field])
                if not value:
                    logger.warning(f"Update user failed: {field} cannot be empty")
                    return jsonify({
                        'success': False,
                        'error': f'{field} cannot be empty'
                    }), 400
                if len(value) > MAX_NAME_LENGTH:
                    logger.warning(f"Update user failed: {field} too long ({len(value)} characters)")
                    return jsonify({
                        'success': False,
                        'error': f'{field} must be {MAX_NAME_LENGTH} characters or less'
                    }), 400

        # Validate phone number length if provided
        if 'phone_number' in data and data['phone_number']:
            phone_number = sanitize_string(data['phone_number'])
            if phone_number and len(phone_number) > MAX_PHONE_LENGTH:
                logger.warning(f"Update user failed: Phone number too long ({len(phone_number)} characters)")
                return jsonify({
                    'success': False,
                    'error': f'Phone number must be {MAX_PHONE_LENGTH} characters or less'
                }), 400

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = sanitize_string(data['first_name'])
        if 'last_name' in data:
            user.last_name = sanitize_string(data['last_name'])
        if 'phone_number' in data:
            user.phone_number = sanitize_string(data['phone_number'])

        db.session.commit()
        logger.info(f"User updated successfully: id={user_id}")

        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update user. Please try again later.'
        }), 500


@auth_bp.route('/check-email', methods=['POST'])
def check_email_availability():
    """Check if an email is available for registration.

    This endpoint allows clients to pre-validate email availability
    before attempting registration, providing immediate feedback to users.
    """
    try:
        data = request.get_json(silent=True)
        logger.debug("Email availability check request received")

        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        email = sanitize_string(data.get('email'))

        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format',
                'available': False
            }), 400

        # Check if email exists
        existing_user = User.query.filter_by(email=email.lower()).first()

        if existing_user:
            logger.debug(f"Email availability check: {email.lower()} is taken")
            return jsonify({
                'success': True,
                'available': False,
                'message': 'Email is already in use'
            }), 200

        logger.debug(f"Email availability check: {email.lower()} is available")
        return jsonify({
            'success': True,
            'available': True,
            'message': 'Email is available'
        }), 200

    except Exception as e:
        logger.error(
            f"Email availability check failed: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'Failed to check email availability. Please try again later.'
        }), 500


@auth_bp.route('/users', methods=['GET'])
def list_users():
    """List all users with pagination (for admin purposes)"""
    try:
        page = request.args.get('page', DEFAULT_PAGE, type=int)
        per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)
        is_active = request.args.get('is_active', type=str)

        # Validate pagination parameters
        if page < 1:
            page = DEFAULT_PAGE
        if per_page < 1 or per_page > MAX_PER_PAGE:
            per_page = DEFAULT_PER_PAGE

        query = User.query

        # Filter by active status if provided
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            query = query.filter_by(is_active=is_active_bool)

        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(
            f"Failed to list users: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve users. Please try again later.'
        }), 500


@auth_bp.route('/db-status', methods=['GET'])
def db_status():
    """Check database connection status for auth module.
    
    This endpoint is useful for debugging registration issues
    and verifying that the database is properly connected.
    
    Returns:
        JSON object with database status and users table info
    """
    try:
        is_healthy, error_msg = check_database_health()
        
        if not is_healthy:
            logger.error(f"Database health check failed: {error_msg}")
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': error_msg,
                'message': 'Database connection failed. Registration may not work.'
            }), 503
        
        # Check if users table exists and get count
        try:
            user_count = User.query.count()
            table_exists = True
        except ProgrammingError:
            db.session.rollback()
            user_count = 0
            table_exists = False
        except Exception as table_error:
            db.session.rollback()
            logger.warning(f"Error checking users table: {str(table_error)}")
            user_count = 0
            table_exists = False
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': {
                'connection': 'ok',
                'users_table_exists': table_exists,
                'user_count': user_count
            },
            'message': 'Database is connected and ready for registration.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database status check failed: {type(e).__name__}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Failed to check database status.'
        }), 500
