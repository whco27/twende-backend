"""Authentication routes for user registration and login"""
from flask import Blueprint, jsonify, request
from models import db, User
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Maximum lengths for database fields
MAX_EMAIL_LENGTH = 255
MAX_NAME_LENGTH = 100
MAX_PHONE_LENGTH = 20


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


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Sanitize inputs (strip whitespace)
        email = sanitize_string(data.get('email'))
        password = data.get('password', '')  # Don't strip password whitespace
        first_name = sanitize_string(data.get('first_name'))
        last_name = sanitize_string(data.get('last_name'))
        phone_number = sanitize_string(data.get('phone_number'))

        # Validate required fields
        if not email:
            return jsonify({
                'success': False,
                'error': 'Missing required field: email'
            }), 400
        if not password:
            return jsonify({
                'success': False,
                'error': 'Missing required field: password'
            }), 400
        if not first_name:
            return jsonify({
                'success': False,
                'error': 'Missing required field: first_name'
            }), 400
        if not last_name:
            return jsonify({
                'success': False,
                'error': 'Missing required field: last_name'
            }), 400

        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400

        # Validate email length
        if len(email) > MAX_EMAIL_LENGTH:
            return jsonify({
                'success': False,
                'error': f'Email must be {MAX_EMAIL_LENGTH} characters or less'
            }), 400

        # Validate name lengths
        if len(first_name) > MAX_NAME_LENGTH:
            return jsonify({
                'success': False,
                'error': f'First name must be {MAX_NAME_LENGTH} characters or less'
            }), 400
        if len(last_name) > MAX_NAME_LENGTH:
            return jsonify({
                'success': False,
                'error': f'Last name must be {MAX_NAME_LENGTH} characters or less'
            }), 400

        # Validate phone number length if provided
        if phone_number and len(phone_number) > MAX_PHONE_LENGTH:
            return jsonify({
                'success': False,
                'error': f'Phone number must be {MAX_PHONE_LENGTH} characters or less'
            }), 400

        # Validate password strength
        if not validate_password(password):
            return jsonify({
                'success': False,
                'error': 'Password must be at least 8 characters long'
            }), 400

        # Check if user already exists
        existing_user = User.query.filter_by(email=email.lower()).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'User with this email already exists'
            }), 409

        # Create new user
        new_user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return user info"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400

        # Find user
        user = User.query.filter_by(email=data['email'].lower()).first()

        if not user or not user.check_password(data['password']):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Account is deactivated'
            }), 403

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
