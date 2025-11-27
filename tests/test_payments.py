"""Tests for payment routes"""


def test_initiate_payment_missing_data(client):
    """Test payment initiation with missing data"""
    response = client.post('/api/payments/initiate', json={})
    assert response.status_code == 400


def test_initiate_payment_booking_not_found(client):
    """Test payment initiation with non-existent booking"""
    response = client.post('/api/payments/initiate', json={
        'booking_id': 9999,
        'phone_number': '0712345678'
    })
    assert response.status_code == 404


def test_initiate_payment_unconfigured(client, sample_user, sample_tour):
    """Test payment initiation when Daraja is not configured"""
    # Create a booking first
    booking_response = client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': '2024-06-15',
        'number_of_guests': 1
    })
    booking_id = booking_response.get_json()['booking']['id']

    # Try to initiate payment (should fail because Daraja is not configured)
    response = client.post('/api/payments/initiate', json={
        'booking_id': booking_id,
        'phone_number': '0712345678'
    })
    # Will return 503 because Daraja credentials are not configured
    assert response.status_code == 503
    assert 'not configured' in response.get_json()['error'].lower()


def test_get_booking_payments(client, sample_user, sample_tour):
    """Test getting payments for a booking"""
    # Create a booking first
    booking_response = client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': '2024-06-15',
        'number_of_guests': 1
    })
    booking_id = booking_response.get_json()['booking']['id']

    response = client.get(f'/api/payments/booking/{booking_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'payments' in data


def test_payment_status_not_found(client):
    """Test checking payment status for non-existent payment"""
    response = client.get('/api/payments/status/nonexistent-checkout-id')
    assert response.status_code == 404
