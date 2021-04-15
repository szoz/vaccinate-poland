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


def test_auth():
    """Test status codes in '/auth' endpoint responses."""
    test_path = '/auth'
    hash_valid = '013c6889f799cd986a735118e1888727d1435f7f623d05d58c61bf2cd8b49ac9' \
                 '0105e5786ceaabd62bbc27336153d0d316b2d13b36804080c44aa6198c533215'
    hash_invalid = 'f34ad4b3ae1e2cf33092e2abb60dc0444781c15d0e2e9ecdb37e4b14176a0164' \
                   '027b05900e09fa0f61a1882e0b89fbfa5dcfcc9765dd2ca4377e2c794837e091'
    response_valid = client.get(test_path, params={'password': 'haslo', 'password_hash': hash_valid})
    params_invalid = [
        {'password': 'haslo', 'password_hash': hash_invalid},
        {'password': 'haslo', 'password_hash': ''},
        {'password': 'haslo'},
        {'password_hash': ''},
        {}
    ]
    responses_invalid = [client.get(test_path, params=params) for params in params_invalid]

    assert response_valid.status_code == 204
    for response in responses_invalid:
        assert response.status_code == 401
