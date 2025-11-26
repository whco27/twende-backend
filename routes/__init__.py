from flask import Blueprint, jsonify, request
from models.tour import db, Tour
from werkzeug.exceptions import NotFound

tours_bp = Blueprint('tours', __name__, url_prefix='/api/tours')

@tours_bp.route('/', methods=['GET'])
def get_tours():
    """Get all tours"""
    try:
        tours = Tour.query.all()
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
