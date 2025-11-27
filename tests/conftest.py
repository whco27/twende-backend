"""Test configuration and fixtures"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['FLASK_ENV'] = 'testing'

from app import app, db
from models import Tour, User, Booking, Payment


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def sample_tour(client):
    """Create a sample tour"""
    with app.app_context():
        tour = Tour(
            title='Test Safari',
            description='A wonderful safari experience',
            price=1500.0,
            duration='3 days',
            location='Masai Mara',
            image_url='https://example.com/safari.jpg',
            available_slots=10
        )
        db.session.add(tour)
        db.session.commit()
        tour_id = tour.id
    return tour_id


@pytest.fixture
def sample_user(client):
    """Create a sample user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            phone_number='0712345678'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    return user_id
