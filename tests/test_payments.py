"""Tests for payment routes"""


def test_initiate_payment_no_data(client):
    """Test payment initiation with no data"""
    response = client.post('/api/payments/initiate', json={})
    assert response.status_code == 400
    data = response.get_json()
    # Empty JSON {} triggers NO_DATA because it evaluates to False
    assert data['error_code'] in ['NO_DATA', 'MISSING_FIELDS']


def test_initiate_payment_empty_phone_number(client, sample_user, sample_tour):
    """Test payment initiation with empty phone number"""
    # Create a booking first
    booking_response = client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': '2024-06-15',
        'number_of_guests': 1
    })
    booking_id = booking_response.get_json()['booking']['id']

    response = client.post('/api/payments/initiate', json={
        'booking_id': booking_id,
        'phone_number': ''
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['error_code'] == 'MISSING_FIELDS'


def test_initiate_payment_booking_not_found(client):
    """Test payment initiation with non-existent booking"""
    response = client.post('/api/payments/initiate', json={
        'booking_id': 9999,
        'phone_number': '0712345678'
    })
    assert response.status_code == 404
    data = response.get_json()
    assert data['error_code'] == 'BOOKING_NOT_FOUND'


def test_initiate_payment_invalid_booking_id(client):
    """Test payment initiation with invalid booking ID format"""
    response = client.post('/api/payments/initiate', json={
        'booking_id': 'invalid',
        'phone_number': '0712345678'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['error_code'] == 'INVALID_BOOKING_ID'


def test_initiate_payment_invalid_phone_number(client, sample_user, sample_tour):
    """Test payment initiation with invalid phone number"""
    # Create a booking first
    booking_response = client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': '2024-06-15',
        'number_of_guests': 1
    })
    booking_id = booking_response.get_json()['booking']['id']

    # Test with too short phone number
    response = client.post('/api/payments/initiate', json={
        'booking_id': booking_id,
        'phone_number': '12345'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['error_code'] == 'INVALID_PHONE'
    assert 'hint' in data


def test_initiate_payment_non_kenyan_phone(client, sample_user, sample_tour):
    """Test payment initiation with non-Kenyan phone number prefix"""
    # Create a booking first
    booking_response = client.post('/api/bookings/', json={
        'user_id': sample_user,
        'tour_id': sample_tour,
        'tour_date': '2024-06-15',
        'number_of_guests': 1
    })
    booking_id = booking_response.get_json()['booking']['id']

    # Test with invalid prefix (not 7XX or 1XX)
    response = client.post('/api/payments/initiate', json={
        'booking_id': booking_id,
        'phone_number': '254200000000'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['error_code'] == 'INVALID_PHONE'


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
    data = response.get_json()
    assert 'not configured' in data['error'].lower()
    assert data['error_code'] == 'SERVICE_NOT_CONFIGURED'


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
    assert 'count' in data


def test_get_booking_payments_not_found(client):
    """Test getting payments for non-existent booking"""
    response = client.get('/api/payments/booking/9999')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error_code'] == 'BOOKING_NOT_FOUND'


def test_payment_status_not_found(client):
    """Test checking payment status for non-existent payment"""
    response = client.get('/api/payments/status/nonexistent-checkout-id')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error_code'] == 'PAYMENT_NOT_FOUND'


def test_config_status_endpoint(client):
    """Test the configuration status endpoint"""
    response = client.get('/api/payments/config/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'config' in data
    assert 'is_configured' in data['config']
    assert 'environment' in data['config']
    assert 'base_url' in data['config']


def test_payment_health_endpoint(client):
    """Test the payment service health endpoint"""
    response = client.get('/api/payments/health')
    # Since Daraja is not configured, it should return 200 with connectivity = not_tested
    assert response.status_code == 200
    data = response.get_json()
    assert 'service' in data
    assert data['service'] == 'M-Pesa Payment Gateway'
    assert 'configured' in data
    assert 'environment' in data


def test_payment_callback_no_data(client):
    """Test payment callback with empty JSON"""
    response = client.post('/api/payments/callback', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['ResultCode'] == 1


def test_payment_callback_payment_not_found(client):
    """Test payment callback for non-existent payment"""
    response = client.post('/api/payments/callback', json={
        'Body': {
            'stkCallback': {
                'MerchantRequestID': 'test-merchant-id',
                'CheckoutRequestID': 'nonexistent-checkout-id',
                'ResultCode': 0,
                'ResultDesc': 'Success'
            }
        }
    })
    assert response.status_code == 404


def test_phone_number_formatting():
    """Test phone number formatting function"""
    from routes.payments import format_phone_number

    # Test various formats
    assert format_phone_number('0712345678') == '254712345678'
    assert format_phone_number('+254712345678') == '254712345678'
    assert format_phone_number('254712345678') == '254712345678'
    assert format_phone_number('712345678') == '254712345678'

    # Test with spaces
    assert format_phone_number(' 0712345678 ') == '254712345678'

    # Test with None
    assert format_phone_number(None) is None


def test_phone_number_validation():
    """Test phone number validation function"""
    from routes.payments import validate_phone_number

    # Valid phone numbers
    assert validate_phone_number('0712345678') is None
    assert validate_phone_number('0112345678') is None
    assert validate_phone_number('254712345678') is None
    assert validate_phone_number('+254712345678') is None

    # Invalid phone numbers
    assert validate_phone_number('') is not None  # Empty
    assert validate_phone_number(None) is not None  # None
    assert validate_phone_number('12345') is not None  # Too short
    assert validate_phone_number('254200000000') is not None  # Invalid prefix
