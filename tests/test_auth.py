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


def test_register_user_without_phone(client):
    """Test user registration without optional phone number"""
    user_data = {
        'email': 'nophone@example.com',
        'password': 'securepass123',
        'first_name': 'Jane',
        'last_name': 'Smith'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['email'] == user_data['email']
    assert data['user']['phone_number'] is None


def test_register_missing_email(client):
    """Test registration with missing email field"""
    user_data = {
        'password': 'securepass123',
        'first_name': 'Jane',
        'last_name': 'Smith'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'email' in data['error'].lower()


def test_register_missing_password(client):
    """Test registration with missing password field"""
    user_data = {
        'email': 'nopass@example.com',
        'first_name': 'Jane',
        'last_name': 'Smith'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'password' in data['error'].lower()


def test_register_missing_first_name(client):
    """Test registration with missing first name field"""
    user_data = {
        'email': 'nofirst@example.com',
        'password': 'securepass123',
        'last_name': 'Smith'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'first_name' in data['error'].lower()


def test_register_missing_last_name(client):
    """Test registration with missing last name field"""
    user_data = {
        'email': 'nolast@example.com',
        'password': 'securepass123',
        'first_name': 'Jane'
    }
    response = client.post('/api/auth/register', json=user_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'last_name' in data['error'].lower()


def test_register_no_data(client):
    """Test registration with no JSON data"""
    response = client.post('/api/auth/register', data='', content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


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


def test_register_duplicate_email_case_insensitive(client):
    """Test registration with existing email but different case"""
    user_data = {
        'email': 'CaseTest@Example.com',
        'password': 'password123',
        'first_name': 'First',
        'last_name': 'User'
    }
    # First registration
    response1 = client.post('/api/auth/register', json=user_data)
    assert response1.status_code == 201

    # Second registration with same email in different case
    user_data['email'] = 'casetest@example.com'
    response2 = client.post('/api/auth/register', json=user_data)
    assert response2.status_code == 409
    assert response2.get_json()['success'] is False


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


def test_login_case_insensitive_email(client, sample_user):
    """Test login with email in different case"""
    response = client.post('/api/auth/login', json={
        'email': 'TEST@EXAMPLE.COM',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


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


def test_login_no_data(client):
    """Test login with no JSON data"""
    response = client.post('/api/auth/login', data='', content_type='application/json')
    assert response.status_code == 400


def test_login_missing_password(client, sample_user):
    """Test login with missing password"""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com'
    })
    assert response.status_code == 400


def test_get_user(client, sample_user):
    """Test getting user info"""
    response = client.get(f'/api/auth/user/{sample_user}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['email'] == 'test@example.com'


def test_get_user_not_found(client):
    """Test getting non-existent user"""
    response = client.get('/api/auth/user/99999')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False


def test_update_user(client, sample_user):
    """Test updating user info"""
    response = client.put(f'/api/auth/user/{sample_user}', json={
        'first_name': 'Johnny',
        'phone_number': '0700000000'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['first_name'] == 'Johnny'


def test_update_user_not_found(client):
    """Test updating non-existent user"""
    response = client.put('/api/auth/user/99999', json={
        'first_name': 'Johnny'
    })
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False


def test_update_user_no_data(client, sample_user):
    """Test updating user with no data"""
    response = client.put(f'/api/auth/user/{sample_user}', data='', content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_check_email_available(client):
    """Test checking availability of an unused email"""
    response = client.post('/api/auth/check-email', json={
        'email': 'available@example.com'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['available'] is True
    assert 'available' in data['message'].lower()


def test_check_email_taken(client, sample_user):
    """Test checking availability of an already registered email"""
    response = client.post('/api/auth/check-email', json={
        'email': 'test@example.com'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['available'] is False
    assert 'already in use' in data['message'].lower()


def test_check_email_case_insensitive(client, sample_user):
    """Test checking availability with different case"""
    response = client.post('/api/auth/check-email', json={
        'email': 'TEST@EXAMPLE.COM'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['available'] is False


def test_check_email_no_data(client):
    """Test checking email without data"""
    response = client.post('/api/auth/check-email', data='', content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_check_email_missing_email(client):
    """Test checking email with missing email field"""
    response = client.post('/api/auth/check-email', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_check_email_invalid_format(client):
    """Test checking email with invalid format"""
    response = client.post('/api/auth/check-email', json={
        'email': 'invalid-email'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['available'] is False
    assert 'invalid' in data['error'].lower()


def test_check_email_with_whitespace(client):
    """Test checking email with whitespace is trimmed"""
    response = client.post('/api/auth/check-email', json={
        'email': '  available@example.com  '
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['available'] is True


def test_list_users(client, sample_user):
    """Test listing users with pagination"""
    response = client.get('/api/auth/users')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'users' in data
    assert 'pagination' in data
    assert len(data['users']) > 0


def test_list_users_with_pagination(client, sample_user):
    """Test listing users with explicit pagination parameters"""
    response = client.get('/api/auth/users?page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['pagination']['page'] == 1
    assert data['pagination']['per_page'] == 10


def test_list_users_filter_by_active(client, sample_user):
    """Test listing users filtered by active status"""
    response = client.get('/api/auth/users?is_active=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # All returned users should be active
    for user in data['users']:
        assert user['is_active'] is True
