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


def test_get_tour_by_title(client, sample_tour):
    """Test getting a tour by exact title"""
    response = client.get('/api/tours/by-title/Test%20Safari')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['tour']['title'] == 'Test Safari'


def test_get_tour_by_title_not_found(client):
    """Test getting a tour by title that doesn't exist"""
    response = client.get('/api/tours/by-title/NonExistent%20Tour')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'error_code' in data
    assert data['error_code'] == 'TOUR_NOT_FOUND'
    assert 'hint' in data


def test_get_tour_by_title_after_seed(client):
    """Test that after seeding, the Masai Mara 3-Day Safari tour can be found by exact title"""
    # Seed the database
    client.post('/api/tours/seed')

    # Get tour by exact title
    response = client.get('/api/tours/by-title/Masai%20Mara%203-Day%20Safari')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['tour']['title'] == 'Masai Mara 3-Day Safari'


def test_create_duplicate_tour(client, sample_tour):
    """Test that creating a tour with duplicate title fails with helpful error"""
    tour_data = {
        'title': 'Test Safari',  # Same title as sample_tour
        'description': 'A duplicate safari',
        'price': 3000.0,
        'duration': '7 days',
        'location': 'Duplicate Location'
    }
    response = client.post('/api/tours/', json=tour_data)
    assert response.status_code == 409
    data = response.get_json()
    assert 'error_code' in data
    assert data['error_code'] == 'DUPLICATE_TITLE'


# Tests for bulk import endpoint
def test_bulk_import_tours(client):
    """Test bulk importing tours"""
    tours_data = {
        'tours': [
            {
                'title': 'Bulk Import Safari 1',
                'description': 'A wonderful safari experience',
                'price': 25000.0,
                'duration': '2 days',
                'location': 'Serengeti'
            },
            {
                'title': 'Bulk Import Safari 2',
                'description': 'Another amazing safari',
                'price': 35000.0,
                'duration': '3 days',
                'location': 'Masai Mara'
            }
        ]
    }
    response = client.post('/api/tours/bulk-import', json=tours_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['created_count'] == 2
    assert data['skipped_count'] == 0
    assert len(data['created_tours']) == 2


def test_bulk_import_no_data(client):
    """Test bulk import with empty JSON object"""
    response = client.post('/api/tours/bulk-import', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    # Empty dict {} evaluates to False in Python (bool({}) == False)
    # so `if not data:` returns True, triggering NO_DATA error
    assert data['error_code'] == 'NO_DATA'


def test_bulk_import_empty_tours(client):
    """Test bulk import with empty tours array"""
    response = client.post('/api/tours/bulk-import', json={'tours': []})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error_code'] == 'NO_TOURS'


def test_bulk_import_missing_required_fields(client):
    """Test bulk import with missing required fields"""
    tours_data = {
        'tours': [
            {
                'title': 'Incomplete Tour',
                'price': 25000.0
                # Missing description, duration, location
            }
        ]
    }
    response = client.post('/api/tours/bulk-import', json=tours_data)
    assert response.status_code == 422  # Unprocessable Entity - validation errors only
    data = response.get_json()
    assert data['success'] is False
    assert data['created_count'] == 0
    assert len(data['validation_errors']) == 1
    assert 'Missing required fields' in data['validation_errors'][0]['error']


def test_bulk_import_invalid_price(client):
    """Test bulk import with invalid price"""
    tours_data = {
        'tours': [
            {
                'title': 'Invalid Price Tour',
                'description': 'A tour with invalid price',
                'price': -500.0,
                'duration': '2 days',
                'location': 'Somewhere'
            }
        ]
    }
    response = client.post('/api/tours/bulk-import', json=tours_data)
    assert response.status_code == 422  # Unprocessable Entity - validation errors only
    data = response.get_json()
    assert data['created_count'] == 0
    assert len(data['validation_errors']) == 1
    assert 'positive number' in data['validation_errors'][0]['error']


def test_bulk_import_skip_existing(client, sample_tour):
    """Test that bulk import skips existing tours by default"""
    tours_data = {
        'tours': [
            {
                'title': 'Test Safari',  # Same as sample_tour
                'description': 'Different description',
                'price': 99999.0,
                'duration': '10 days',
                'location': 'Different Location'
            }
        ]
    }
    response = client.post('/api/tours/bulk-import', json=tours_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['created_count'] == 0
    assert data['skipped_count'] == 1


def test_bulk_import_update_existing(client, sample_tour):
    """Test that bulk import can update existing tours"""
    tours_data = {
        'tours': [
            {
                'title': 'Test Safari',  # Same as sample_tour
                'description': 'Updated description',
                'price': 99999.0,
                'duration': '10 days',
                'location': 'Updated Location'
            }
        ],
        'update_existing': True
    }
    response = client.post('/api/tours/bulk-import', json=tours_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['updated_count'] == 1
    assert data['updated_tours'][0]['price'] == 99999.0
    assert data['updated_tours'][0]['description'] == 'Updated description'


def test_bulk_import_mixed_valid_invalid(client):
    """Test bulk import with mix of valid and invalid tours"""
    tours_data = {
        'tours': [
            {
                'title': 'Valid Tour',
                'description': 'A valid tour',
                'price': 25000.0,
                'duration': '2 days',
                'location': 'Valid Location'
            },
            {
                'title': 'Invalid Tour',
                # Missing required fields
                'price': 30000.0
            }
        ]
    }
    response = client.post('/api/tours/bulk-import', json=tours_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['created_count'] == 1
    assert data['error_count'] == 1
