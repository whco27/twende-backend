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


def test_get_tours_with_pagination(client, sample_tour):
    """Test getting tours with pagination"""
    response = client.get('/api/tours/?page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'tours' in data
    assert 'pagination' in data
    assert data['pagination']['page'] == 1
    assert data['pagination']['per_page'] == 10
    assert len(data['tours']) > 0


def test_get_tours_filter_by_location(client, sample_tour):
    """Test getting tours filtered by location"""
    response = client.get('/api/tours/?location=Masai')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert 'Masai' in data[0]['location']


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


def test_search_tours_by_title(client, sample_tour):
    """Test searching tours by title"""
    response = client.get('/api/tours/search?title=Safari')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'tours' in data
    assert 'pagination' in data
    assert len(data['tours']) > 0
    assert 'Safari' in data['tours'][0]['title']


def test_search_tours_by_location(client, sample_tour):
    """Test searching tours by location"""
    response = client.get('/api/tours/search?location=Masai')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['tours']) > 0
    assert 'Masai' in data['tours'][0]['location']


def test_search_tours_by_price_range(client, sample_tour):
    """Test searching tours by price range"""
    response = client.get('/api/tours/search?min_price=1000&max_price=2000')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['tours']) > 0
    for tour in data['tours']:
        assert tour['price'] >= 1000
        assert tour['price'] <= 2000


def test_search_tours_no_results(client):
    """Test searching tours with no matching results"""
    response = client.get('/api/tours/search?title=NonExistentTour')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['tours']) == 0


def test_seed_tours(client):
    """Test seeding default tours"""
    response = client.post('/api/tours/seed')
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'created_tours' in data
    assert 'existing_tours' in data
    assert len(data['created_tours']) > 0


def test_seed_tours_idempotent(client):
    """Test that seeding tours is idempotent (doesn't create duplicates)"""
    # First seed
    response1 = client.post('/api/tours/seed')
    assert response1.status_code == 201
    data1 = response1.get_json()
    created_count = len(data1['created_tours'])

    # Second seed - should not create new tours
    response2 = client.post('/api/tours/seed')
    assert response2.status_code == 200  # 200 when all already exist
    data2 = response2.get_json()
    assert data2['success'] is True
    assert len(data2['created_tours']) == 0
    assert len(data2['existing_tours']) == created_count


def test_seed_then_search_masai_mara(client):
    """Test that after seeding, the Masai Mara tour can be found"""
    # Seed the database
    client.post('/api/tours/seed')

    # Search for Masai Mara tour
    response = client.get('/api/tours/search?title=Masai%20Mara')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['tours']) > 0
    assert 'Masai Mara' in data['tours'][0]['title']
