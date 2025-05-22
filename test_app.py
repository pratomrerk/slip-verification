import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the /health-check route."""
    response = client.get('/health-check')
    assert response.status_code == 200
    assert response.json == {'statusCode': 200, 'message': 'OK'}
