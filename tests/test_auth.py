"""Tests for authentication routes"""


def test_register_user(client):
    """Test user registration"""
    user_data = {
        'email': 'newuser@example.com',
        'password': 'securepass123',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'phone_number': '0722334455'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['email'] == user_data['email']


def test_register_duplicate_email(client):
    """Test registration with existing email"""
    user_data = {
        'email': 'duplicate@example.com',
        'password': 'password123',
        'first_name': 'First',
        'last_name': 'User'
    }
    # First registration
    client.post('/api/auth/register', json=user_data)
    # Second registration with same email
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 409
    assert response.get_json()['success'] is False


def test_register_invalid_email(client):
    """Test registration with invalid email"""
    user_data = {
        'email': 'invalid-email',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400


def test_register_weak_password(client):
    """Test registration with weak password"""
    user_data = {
        'email': 'test@example.com',
        'password': 'short',
        'first_name': 'Test',
        'last_name': 'User'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400


def test_register_email_with_whitespace(client):
    """Test registration with email that has leading/trailing whitespace"""
    user_data = {
        'email': '  whitespace@example.com  ',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    # Email should be trimmed
    assert data['user']['email'] == 'whitespace@example.com'


def test_register_email_too_long(client):
    """Test registration with email exceeding maximum length"""
    long_email = 'a' * 250 + '@example.com'
    user_data = {
        'email': long_email,
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert '255 characters' in data['error']


def test_register_name_too_long(client):
    """Test registration with first name exceeding maximum length"""
    user_data = {
        'email': 'longname@example.com',
        'password': 'password123',
        'first_name': 'A' * 101,
        'last_name': 'User'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert '100 characters' in data['error']


def test_register_phone_too_long(client):
    """Test registration with phone number exceeding maximum length"""
    user_data = {
        'email': 'longphone@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '0' * 21
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert '20 characters' in data['error']


def test_register_names_trimmed(client):
    """Test that first and last names are trimmed of whitespace"""
    user_data = {
        'email': 'trimmed@example.com',
        'password': 'password123',
        'first_name': '  John  ',
        'last_name': '  Doe  '
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['user']['first_name'] == 'John'
    assert data['user']['last_name'] == 'Doe'


def test_login_success(client, sample_user):
    """Test successful login"""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'user' in data


def test_login_wrong_password(client, sample_user):
    """Test login with wrong password"""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert response.get_json()['success'] is False


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password123'
    })
    assert response.status_code == 401


def test_get_user(client, sample_user):
    """Test getting user info"""
    response = client.get(f'/api/auth/user/{sample_user}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['email'] == 'test@example.com'


def test_update_user(client, sample_user):
    """Test updating user info"""
    response = client.put(f'/api/auth/user/{sample_user}', json={
        'first_name': 'Johnny',
        'phone_number': '0700000000'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['first_name'] == 'Johnny'
