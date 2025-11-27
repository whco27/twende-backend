"""Tests for tour routes"""


def test_root_endpoint(client):
    """Test root endpoint returns API info"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'endpoints' in data


def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'database' in data


def test_get_tours_empty(client):
    """Test getting tours when none exist"""
    response = client.get('/api/tours/')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_tour(client):
    """Test creating a new tour"""
    tour_data = {
        'title': 'Safari Adventure',
        'description': 'An amazing safari',
        'price': 2000.0,
        'duration': '5 days',
        'location': 'Serengeti'
    }
    response = client.post('/api/tours/', json=tour_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == tour_data['title']
    assert data['price'] == tour_data['price']


def test_get_tour(client, sample_tour):
    """Test getting a specific tour"""
    response = client.get(f'/api/tours/{sample_tour}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Test Safari'


def test_get_tour_not_found(client):
    """Test getting a non-existent tour"""
    response = client.get('/api/tours/9999')
    assert response.status_code == 404


def test_update_tour(client, sample_tour):
    """Test updating a tour"""
    update_data = {'title': 'Updated Safari'}
    response = client.put(f'/api/tours/{sample_tour}', json=update_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Updated Safari'


def test_delete_tour(client, sample_tour):
    """Test deleting a tour"""
    response = client.delete(f'/api/tours/{sample_tour}')
    assert response.status_code == 200

    # Verify tour is deleted
    response = client.get(f'/api/tours/{sample_tour}')
    assert response.status_code == 404
