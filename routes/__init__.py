from flask import Blueprint, jsonify, request
from models.tour import db, Tour
from werkzeug.exceptions import NotFound

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
