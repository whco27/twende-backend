"""Tests for frontend static file serving"""
import os


def test_root_endpoint_without_frontend(client):
    """Test root endpoint returns API info when no frontend is deployed"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'endpoints' in data
    assert data['message'] == 'Twende Tours API running'


def test_404_api_route_returns_json(client):
    """Test that 404 on API routes returns JSON error"""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Not found'


def test_404_non_api_route_without_frontend(client):
    """Test that 404 on non-API routes returns appropriate message when no frontend"""
    response = client.get('/some-spa-route')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'Frontend not deployed' in data.get('message', '')


def test_static_file_serving(client):
    """Test that static files are served from public directory"""
    from app import STATIC_FOLDER

    # Create a test static file
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    test_file_path = os.path.join(STATIC_FOLDER, 'test.txt')
    try:
        with open(test_file_path, 'w') as f:
            f.write('test content')

        response = client.get('/test.txt')
        assert response.status_code == 200
        assert b'test content' in response.data
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


def test_root_serves_index_html_when_exists(client):
    """Test that root serves index.html when frontend is deployed"""
    from app import STATIC_FOLDER

    # Create a test index.html
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    try:
        with open(index_path, 'w') as f:
            f.write('<!DOCTYPE html><html><body>Frontend App</body></html>')

        response = client.get('/')
        assert response.status_code == 200
        assert b'Frontend App' in response.data
    finally:
        # Cleanup
        if os.path.exists(index_path):
            os.remove(index_path)


def test_spa_route_serves_index_html_when_exists(client):
    """Test that SPA routes serve index.html for client-side routing"""
    from app import STATIC_FOLDER

    # Create a test index.html
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    try:
        with open(index_path, 'w') as f:
            f.write('<!DOCTYPE html><html><body>SPA Frontend</body></html>')

        # Test various SPA routes
        for route in ['/tours', '/about', '/booking/123', '/user/profile']:
            response = client.get(route)
            assert response.status_code == 200, f"Failed for route {route}"
            assert b'SPA Frontend' in response.data, f"Failed for route {route}"
    finally:
        # Cleanup
        if os.path.exists(index_path):
            os.remove(index_path)


def test_api_routes_not_affected_by_frontend(client):
    """Test that API routes work normally regardless of frontend deployment"""
    # Test tours API
    response = client.get('/api/tours/')
    assert response.status_code == 200

    # Test health endpoint
    response = client.get('/health')
    assert response.status_code == 200


def test_daraja_static_files_served(client):
    """Test that Daraja payment files are served from public/daraja directory"""
    from app import STATIC_FOLDER

    daraja_dir = os.path.join(STATIC_FOLDER, 'daraja')

    # Verify the daraja payment page exists and is served
    if os.path.exists(os.path.join(daraja_dir, 'payment.html')):
        response = client.get('/daraja/payment.html')
        assert response.status_code == 200
        assert b'M-Pesa' in response.data or b'payment' in response.data.lower()


def test_daraja_subdirectory_serving(client):
    """Test that files in daraja subdirectory are served correctly"""
    from app import STATIC_FOLDER

    daraja_dir = os.path.join(STATIC_FOLDER, 'daraja')
    os.makedirs(daraja_dir, exist_ok=True)

    # Create a test file in daraja directory
    test_file_path = os.path.join(daraja_dir, 'test_daraja.txt')
    try:
        with open(test_file_path, 'w') as f:
            f.write('daraja test content')

        response = client.get('/daraja/test_daraja.txt')
        assert response.status_code == 200
        assert b'daraja test content' in response.data
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
