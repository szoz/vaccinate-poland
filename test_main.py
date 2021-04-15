from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root():
    """Test '/' endpoint basic response."""
    response = client.get('/')

    assert response.status_code == 200
    assert response.json() == {'message': 'Hello world!'}


def test_method():
    """Test status codes and returned methods in '/method' responses."""
    test_path = '/method'
    methods_to_status = {
        'GET': 200,
        'POST': 201,
        'DELETE': 200,
        'PUT': 200,
        'OPTIONS': 200
    }
    responses = [client.request(method, test_path) for method in methods_to_status.keys()]

    for case, response in zip(methods_to_status.items(), responses):
        assert response.status_code == case[1]
        assert response.json().get('method') == case[0]
