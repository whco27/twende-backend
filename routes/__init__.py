from flask import Blueprint, jsonify, request
from models.tour import db, Tour
from werkzeug.exceptions import NotFound
from sqlalchemy.exc import IntegrityError
from data.tours_data import DEFAULT_TOURS

# Import additional blueprints
from .auth import auth_bp
from .bookings import bookings_bp
from .payments import payments_bp
from .trip_schedules import trip_schedules_bp, trip_scheduler_bp

tours_bp = Blueprint('tours', __name__, url_prefix='/api/tours')

# Default pagination settings
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def validate_tour_string_fields(data, fields):
    """Validate that string fields are not empty.
    
    Args:
        data: Dictionary containing the data to validate
        fields: List of field names to validate
        
    Returns:
        tuple: (is_valid, error_message) - is_valid is True if all fields are valid,
               error_message contains the error description if validation fails
    """
    for field in fields:
        value = data.get(field)
        if value is None or not str(value).strip():
            return False, f'{field} cannot be empty'
    return True, None


def validate_tour_price(price_value):
    """Validate that price is a positive number.
    
    Args:
        price_value: The price value to validate
        
    Returns:
        tuple: (is_valid, price_or_error) - if valid, returns (True, float_price),
               if invalid, returns (False, error_message)
    """
    try:
        price = float(price_value)
        if price <= 0:
            return False, 'Price must be a positive number'
        return True, price
    except (ValueError, TypeError):
        return False, 'Invalid price format. Price must be a number'


def validate_tour_available_slots(slots_value, default=10):
    """Validate that available_slots is a non-negative integer.
    
    Args:
        slots_value: The available_slots value to validate
        default: Default value if slots_value is None
        
    Returns:
        tuple: (is_valid, slots_or_error) - if valid, returns (True, int_slots),
               if invalid, returns (False, error_message)
    """
    if slots_value is None:
        return True, default
    try:
        slots = int(slots_value)
        if slots < 0:
            return False, 'available_slots cannot be negative'
        return True, slots
    except (ValueError, TypeError):
        return False, 'Invalid available_slots format. Must be a non-negative integer'


@tours_bp.route('/', methods=['GET'])
def get_tours():
    """Get all tours with optional pagination"""
    try:
        # Check if pagination is requested
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)
        location = request.args.get('location')

        query = Tour.query

        # Filter by location if provided
        if location:
            query = query.filter(Tour.location.ilike(f'%{location}%'))

        # If pagination parameters are provided, return paginated results
        if page is not None:
            if page < 1:
                page = DEFAULT_PAGE
            if per_page is None or per_page < 1 or per_page > MAX_PER_PAGE:
                per_page = DEFAULT_PER_PAGE

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            return jsonify({
                'success': True,
                'tours': [tour.to_dict() for tour in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }), 200

        # Return all tours for backward compatibility
        tours = query.all()
        return jsonify([tour.to_dict() for tour in tours]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tours_bp.route('/count', methods=['GET'])
def get_tours_count():
    """Get the total count of tours in the database.
    
    This endpoint is useful for frontend to check if tours data exists
    before making additional API calls.
    
    Returns:
        JSON object with:
        - success: boolean
        - count: total number of tours
        - has_tours: boolean indicating if there are any tours
    """
    try:
        count = Tour.query.count()
        return jsonify({
            'success': True,
            'count': count,
            'has_tours': count > 0
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tours_bp.route('/<int:tour_id>', methods=['GET'])
def get_tour(tour_id):
    """Get a specific tour by ID"""
    try:
        tour = Tour.query.get_or_404(tour_id)
        return jsonify(tour.to_dict()), 200
    except NotFound:
        # Provide helpful error with available tour IDs
        total_tours = Tour.query.count()
        if total_tours == 0:
            return jsonify({
                'error': 'Tour not found',
                'error_code': 'TOUR_NOT_FOUND',
                'tour_id': tour_id,
                'hint': 'No tours exist in the database. Use POST /api/tours/seed to create default tours.'
            }), 404
        # Get a sample of available tour IDs
        sample_tours = Tour.query.with_entities(Tour.id, Tour.title).limit(5).all()
        return jsonify({
            'error': 'Tour not found',
            'error_code': 'TOUR_NOT_FOUND',
            'tour_id': tour_id,
            'hint': f'Tour ID {tour_id} does not exist. There are {total_tours} tours available.',
            'available_tours_sample': [{'id': t.id, 'title': t.title} for t in sample_tours]
        }), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tours_bp.route('/by-title/<path:title>', methods=['GET'])
def get_tour_by_title(title):
    """Get a specific tour by exact title.
    
    Args:
        title: The exact title of the tour to find
    
    Returns:
        JSON object with tour details if found, error otherwise
    """
    try:
        tour = Tour.query.filter(Tour.title == title).first()
        if tour:
            return jsonify({
                'success': True,
                'tour': tour.to_dict()
            }), 200
        
        # Tour not found - provide helpful guidance (limit suggestions for performance)
        available_tours = Tour.query.with_entities(Tour.title).limit(10).all()
        available_titles = [t.title for t in available_tours]
        
        return jsonify({
            'success': False,
            'error': f'Tour "{title}" not found in backend database',
            'error_code': 'TOUR_NOT_FOUND',
            'hint': 'Use POST /api/tours/seed to create default tours, or POST /api/tours/ to add a new tour.',
            'available_tours': available_titles
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tours_bp.route('/', methods=['POST'])
def create_tour():
    """Create a new tour"""
    try:
        data = request.get_json(silent=True)
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['title', 'description', 'price', 'duration', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate that string fields are not empty
        string_fields = ['title', 'description', 'duration', 'location']
        is_valid, error_msg = validate_tour_string_fields(data, string_fields)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate price is a positive number
        is_valid, price_result = validate_tour_price(data['price'])
        if not is_valid:
            return jsonify({'error': price_result}), 400
        price = price_result
        
        # Validate available_slots if provided
        is_valid, slots_result = validate_tour_available_slots(data.get('available_slots'))
        if not is_valid:
            return jsonify({'error': slots_result}), 400
        available_slots = slots_result
        
        # Check if tour with same title already exists (provides better error response)
        # Note: IntegrityError catch below handles race condition at database level
        existing_tour = Tour.query.filter(Tour.title == data['title']).first()
        if existing_tour:
            return jsonify({
                'error': f'Tour with title "{data["title"]}" already exists',
                'error_code': 'DUPLICATE_TITLE',
                'existing_tour': existing_tour.to_dict()
            }), 409
        
        new_tour = Tour(
            title=data['title'].strip(),
            description=data['description'].strip(),
            price=price,
            duration=data['duration'].strip(),
            location=data['location'].strip(),
            image_url=data.get('image_url', ''),
            available_slots=available_slots
        )
        
        db.session.add(new_tour)
        db.session.commit()
        
        return jsonify(new_tour.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'error': 'A tour with this title already exists',
            'error_code': 'DUPLICATE_TITLE'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tours_bp.route('/<int:tour_id>', methods=['PUT'])
def update_tour(tour_id):
    """Update an existing tour"""
    try:
        tour = Tour.query.get_or_404(tour_id)
        data = request.get_json(silent=True)
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate string fields if provided
        string_fields = ['title', 'description', 'duration', 'location']
        # Filter to only include fields that are present in the data
        fields_to_validate = [f for f in string_fields if f in data]
        if fields_to_validate:
            is_valid, error_msg = validate_tour_string_fields(data, fields_to_validate)
            if not is_valid:
                return jsonify({'error': error_msg}), 400
        
        # Validate price if provided
        if 'price' in data:
            is_valid, price_result = validate_tour_price(data['price'])
            if not is_valid:
                return jsonify({'error': price_result}), 400
        
        # Validate available_slots if provided
        if 'available_slots' in data:
            is_valid, slots_result = validate_tour_available_slots(data['available_slots'])
            if not is_valid:
                return jsonify({'error': slots_result}), 400
        
        # Update fields if provided
        if 'title' in data:
            tour.title = data['title'].strip()
        if 'description' in data:
            tour.description = data['description'].strip()
        if 'price' in data:
            tour.price = float(data['price'])
        if 'duration' in data:
            tour.duration = data['duration'].strip()
        if 'location' in data:
            tour.location = data['location'].strip()
        if 'image_url' in data:
            tour.image_url = data['image_url']
        if 'available_slots' in data:
            tour.available_slots = int(data['available_slots'])
        
        db.session.commit()
        
        return jsonify(tour.to_dict()), 200
    except NotFound:
        return jsonify({'error': 'Tour not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tours_bp.route('/<int:tour_id>', methods=['DELETE'])
def delete_tour(tour_id):
    """Delete a tour"""
    try:
        tour = Tour.query.get_or_404(tour_id)
        db.session.delete(tour)
        db.session.commit()
        
        return jsonify({'message': 'Tour deleted successfully'}), 200
    except NotFound:
        return jsonify({'error': 'Tour not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tours_bp.route('/search', methods=['GET'])
def search_tours():
    """Search tours by title or other criteria.
    
    Query Parameters:
        title: Search by tour title (partial match, case-insensitive)
        location: Filter by location (partial match, case-insensitive)
        min_price: Minimum price filter
        max_price: Maximum price filter
        page: Page number for pagination
        per_page: Results per page
    
    Returns:
        JSON object with matching tours and pagination info
    """
    try:
        title = request.args.get('title')
        location = request.args.get('location')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        page = request.args.get('page', DEFAULT_PAGE, type=int)
        per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)

        # Validate pagination parameters
        if page < 1:
            page = DEFAULT_PAGE
        if per_page < 1 or per_page > MAX_PER_PAGE:
            per_page = DEFAULT_PER_PAGE

        query = Tour.query

        # Apply filters
        if title:
            query = query.filter(Tour.title.ilike(f'%{title}%'))
        if location:
            query = query.filter(Tour.location.ilike(f'%{location}%'))
        if min_price is not None:
            query = query.filter(Tour.price >= min_price)
        if max_price is not None:
            query = query.filter(Tour.price <= max_price)

        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'tours': [tour.to_dict() for tour in pagination.items],
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tours_bp.route('/seed', methods=['POST'])
def seed_tours():
    """Seed the database with default tours.
    
    This endpoint creates a set of default tours if they don't exist.
    Used to ensure the database has tour data for frontend integration.
    The tour data is loaded from data/tours_data.py which contains
    comprehensive Kenyan safari and travel experiences.
    
    Returns:
        JSON object containing:
        - success: boolean indicating operation success
        - message: summary of operation (e.g., "Created 5 new tours, 3 already existed")
        - created_tours: array of newly created tour objects
        - existing_tours: array of tours that already existed
        - total_tours: total count of tours (created + existing)
        
        Status codes:
        - 201: At least one tour was created
        - 200: All tours already existed
        - 500: Server error
    """
    try:
        created_tours = []
        existing_tours = []

        for tour_data in DEFAULT_TOURS:
            # Check if tour with same title already exists
            existing = Tour.query.filter(Tour.title.ilike(tour_data['title'])).first()
            if existing:
                existing_tours.append(existing.to_dict())
            else:
                new_tour = Tour(**tour_data)
                db.session.add(new_tour)
                db.session.flush()  # Get the ID before commit
                created_tours.append(new_tour.to_dict())

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Created {len(created_tours)} new tours, {len(existing_tours)} already existed',
            'created_tours': created_tours,
            'existing_tours': existing_tours,
            'total_tours': len(created_tours) + len(existing_tours)
        }), 201 if created_tours else 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tours_bp.route('/bulk-import', methods=['POST'])
def bulk_import_tours():
    """Bulk import tours from frontend data.
    
    This endpoint receives an array of tour objects and creates them in the database.
    Existing tours (matched by title) are skipped or updated based on the 'update_existing' flag.
    
    Request body:
        {
            "tours": [
                {
                    "title": "Tour Name",
                    "description": "Tour description",
                    "price": 45000.0,
                    "duration": "3 days",
                    "location": "Location",
                    "image_url": "https://...",  // optional
                    "available_slots": 20  // optional, defaults to 10
                },
                ...
            ],
            "update_existing": false  // optional, if true updates existing tours
        }
    
    Returns:
        JSON object with created, updated, and skipped tour counts
    """
    try:
        data = request.get_json(silent=True)
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'error_code': 'NO_DATA'
            }), 400
        
        tours_data = data.get('tours', [])
        update_existing = data.get('update_existing', False)
        
        if not tours_data:
            return jsonify({
                'success': False,
                'error': 'No tours provided in request',
                'error_code': 'NO_TOURS'
            }), 400
        
        if not isinstance(tours_data, list):
            return jsonify({
                'success': False,
                'error': 'Tours must be an array',
                'error_code': 'INVALID_FORMAT'
            }), 400
        
        # Required fields for validation
        required_fields = ['title', 'description', 'price', 'duration', 'location']
        
        created_tours = []
        updated_tours = []
        skipped_tours = []
        validation_errors = []
        
        for i, tour_data in enumerate(tours_data):
            # Validate required fields
            missing_fields = [f for f in required_fields if f not in tour_data or not tour_data[f]]
            if missing_fields:
                validation_errors.append({
                    'index': i,
                    'title': tour_data.get('title', f'Tour at index {i}'),
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                })
                continue
            
            # Validate price is a positive number
            try:
                price = float(tour_data['price'])
                if price <= 0:
                    validation_errors.append({
                        'index': i,
                        'title': tour_data.get('title'),
                        'error': 'Price must be a positive number'
                    })
                    continue
            except (ValueError, TypeError):
                validation_errors.append({
                    'index': i,
                    'title': tour_data.get('title'),
                    'error': 'Invalid price format'
                })
                continue
            
            # Check if tour with same title exists
            existing = Tour.query.filter(Tour.title == tour_data['title']).first()
            
            if existing:
                if update_existing:
                    # Update existing tour
                    existing.description = tour_data['description']
                    existing.price = price
                    existing.duration = tour_data['duration']
                    existing.location = tour_data['location']
                    existing.image_url = tour_data.get('image_url', existing.image_url)
                    existing.available_slots = tour_data.get('available_slots', existing.available_slots)
                    updated_tours.append(existing.to_dict())
                else:
                    skipped_tours.append({
                        'title': tour_data['title'],
                        'reason': 'Already exists'
                    })
            else:
                # Create new tour
                new_tour = Tour(
                    title=tour_data['title'],
                    description=tour_data['description'],
                    price=price,
                    duration=tour_data['duration'],
                    location=tour_data['location'],
                    image_url=tour_data.get('image_url', ''),
                    available_slots=tour_data.get('available_slots', 10)
                )
                db.session.add(new_tour)
                db.session.flush()
                created_tours.append(new_tour.to_dict())
        
        db.session.commit()
        
        # Determine appropriate status code
        # 201: At least one tour was created or updated
        # 200: All tours were skipped (already existed)
        # 422: Only validation errors occurred (no successful operations)
        if created_tours or updated_tours:
            status_code = 201
        elif validation_errors and not skipped_tours:
            status_code = 422  # Unprocessable Entity - all tours had validation errors
        else:
            status_code = 200  # All tours already existed
        
        return jsonify({
            'success': len(validation_errors) == 0 or len(created_tours) > 0 or len(updated_tours) > 0,
            'message': f'Created {len(created_tours)}, updated {len(updated_tours)}, skipped {len(skipped_tours)} tours',
            'created_count': len(created_tours),
            'updated_count': len(updated_tours),
            'skipped_count': len(skipped_tours),
            'error_count': len(validation_errors),
            'created_tours': created_tours,
            'updated_tours': updated_tours,
            'skipped_tours': skipped_tours,
            'validation_errors': validation_errors
        }), status_code
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
