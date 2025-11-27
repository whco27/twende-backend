from flask import Blueprint, jsonify, request
from models.tour import db, Tour
from werkzeug.exceptions import NotFound
from sqlalchemy.exc import IntegrityError

# Import additional blueprints
from .auth import auth_bp
from .bookings import bookings_bp
from .payments import payments_bp

tours_bp = Blueprint('tours', __name__, url_prefix='/api/tours')

# Default pagination settings
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


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

@tours_bp.route('/<int:tour_id>', methods=['GET'])
def get_tour(tour_id):
    """Get a specific tour by ID"""
    try:
        tour = Tour.query.get_or_404(tour_id)
        return jsonify(tour.to_dict()), 200
    except NotFound:
        return jsonify({'error': 'Tour not found'}), 404
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
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['title', 'description', 'price', 'duration', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
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
            title=data['title'],
            description=data['description'],
            price=data['price'],
            duration=data['duration'],
            location=data['location'],
            image_url=data.get('image_url', ''),
            available_slots=data.get('available_slots', 10)
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
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields if provided
        if 'title' in data:
            tour.title = data['title']
        if 'description' in data:
            tour.description = data['description']
        if 'price' in data:
            tour.price = data['price']
        if 'duration' in data:
            tour.duration = data['duration']
        if 'location' in data:
            tour.location = data['location']
        if 'image_url' in data:
            tour.image_url = data['image_url']
        if 'available_slots' in data:
            tour.available_slots = data['available_slots']
        
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
    
    Returns:
        JSON object with the created or existing tours
    """
    try:
        # Default tours to seed
        default_tours = [
            {
                'title': 'Masai Mara 3-Day Safari',
                'description': 'Experience the world-famous Masai Mara Game Reserve with expert guides. Witness the Great Migration and spot the Big Five in their natural habitat.',
                'price': 45000.0,
                'duration': '3 days',
                'location': 'Masai Mara',
                'image_url': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800',
                'available_slots': 20
            },
            {
                'title': 'Mount Kenya Hiking Adventure',
                'description': 'Conquer Africa\'s second-highest peak. This challenging trek offers stunning views and unique alpine ecosystems.',
                'price': 65000.0,
                'duration': '5 days',
                'location': 'Mount Kenya',
                'image_url': 'https://images.unsplash.com/photo-1489493887464-892be6d1daae?w=800',
                'available_slots': 15
            },
            {
                'title': 'Amboseli National Park Tour',
                'description': 'Enjoy breathtaking views of Mount Kilimanjaro while observing elephants and other wildlife in Amboseli.',
                'price': 35000.0,
                'duration': '2 days',
                'location': 'Amboseli',
                'image_url': 'https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=800',
                'available_slots': 25
            },
            {
                'title': 'Diani Beach Getaway',
                'description': 'Relax on the pristine white sands of Diani Beach. Enjoy water sports, snorkeling, and coastal Swahili cuisine.',
                'price': 28000.0,
                'duration': '4 days',
                'location': 'Diani Beach',
                'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800',
                'available_slots': 30
            },
            {
                'title': 'Lake Nakuru Bird Watching',
                'description': 'Discover the pink flamingos and diverse bird species at Lake Nakuru. Also spot rhinos, lions, and leopards.',
                'price': 22000.0,
                'duration': '1 day',
                'location': 'Lake Nakuru',
                'image_url': 'https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=800',
                'available_slots': 40
            },
            {
                'title': 'Tsavo East & West Safari',
                'description': 'Explore Kenya\'s largest national park. See the famous red elephants, diverse landscapes, and Mzima Springs.',
                'price': 55000.0,
                'duration': '4 days',
                'location': 'Tsavo',
                'image_url': 'https://images.unsplash.com/photo-1534177616064-ef1b8e0f4fa4?w=800',
                'available_slots': 18
            }
        ]

        created_tours = []
        existing_tours = []

        for tour_data in default_tours:
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
