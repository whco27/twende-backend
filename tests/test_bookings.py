"""Tests for booking routes"""
from datetime import date, timedelta


# Get a future date for testing (30 days from now)
def get_future_date():
    return (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')


def test_create_booking(client, sample_user, sample_tour):
    """Test creating a booking"""
    booking_data = {
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 2
    }
    response = client.post('/api/bookings/', json=booking_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['booking']['user_id'] == sample_user
    assert data['booking']['tour_id'] == sample_tour


def test_get_bookings(client, sample_user, sample_tour):
    """Test getting all bookings"""
    # Create a booking first
    client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 1
    })

    response = client.get('/api/bookings/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['bookings']) > 0


def test_get_bookings_with_pagination(client, sample_user, sample_tour):
    """Test getting bookings with pagination"""
    # Create a booking first
    client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 1
    })

    response = client.get('/api/bookings/?page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'pagination' in data
    assert data['pagination']['page'] == 1
    assert data['pagination']['per_page'] == 10


def test_get_user_bookings(client, sample_user, sample_tour):
    """Test getting bookings for a specific user"""
    # Create a booking
    client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 1
    })

    response = client.get(f'/api/bookings/user/{sample_user}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['bookings']) > 0


def test_cancel_booking(client, sample_user, sample_tour):
    """Test cancelling a booking"""
    # Create a booking
    create_response = client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 2
    })
    booking_id = create_response.get_json()['booking']['id']

    # Cancel the booking
    response = client.post(f'/api/bookings/{booking_id}/cancel')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['booking']['status'] == 'cancelled'


def test_delete_booking(client, sample_user, sample_tour):
    """Test deleting a booking"""
    # Create a booking
    create_response = client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 2
    })
    booking_id = create_response.get_json()['booking']['id']

    # Delete the booking
    response = client.delete(f'/api/bookings/{booking_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['message'] == 'Booking deleted successfully'

    # Verify booking is deleted
    response = client.get(f'/api/bookings/{booking_id}')
    assert response.status_code == 404


def test_delete_booking_not_found(client):
    """Test deleting a non-existent booking"""
    response = client.delete('/api/bookings/9999')
    assert response.status_code == 404


def test_booking_past_date(client, sample_user, sample_tour):
    """Test that booking a tour for a past date fails"""
    past_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    booking_data = {
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': past_date,
        'number_of_guests': 2
    }
    response = client.post('/api/bookings/', json=booking_data)
    assert response.status_code == 400
    assert 'past date' in response.get_json()['error'].lower()


def test_booking_insufficient_slots(client, sample_user, sample_tour):
    """Test booking with more guests than available slots"""
    booking_data = {
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 100  # More than available slots (10)
    }
    response = client.post('/api/bookings/', json=booking_data)
    assert response.status_code == 400
    assert 'slots' in response.get_json()['error'].lower()


def test_booking_invalid_guests(client, sample_user, sample_tour):
    """Test booking with invalid number_of_guests value"""
    booking_data = {
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': get_future_date(),
        'number_of_guests': 'invalid'
    }
    response = client.post('/api/bookings/', json=booking_data)
    assert response.status_code == 400
    assert 'invalid' in response.get_json()['error'].lower()


def test_booking_tour_not_found(client, sample_user):
    """Test creating booking with non-existent tour returns error code"""
    booking_data = {
        'user_id': sample_user,
        'tour_id': 9999,  # Non-existent tour
        'tour_date': get_future_date(),
        'number_of_guests': 1
    }
    response = client.post('/api/bookings/', json=booking_data)
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert data['error_code'] == 'TOUR_NOT_FOUND'
    assert 'hint' in data

