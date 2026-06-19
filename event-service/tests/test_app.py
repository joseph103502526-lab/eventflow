import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'event-service'

def test_get_events(client):
    response = client.get('/events')
    assert response.status_code == 200
    data = response.get_json()
    assert 'events' in data
    assert len(data['events']) > 0
