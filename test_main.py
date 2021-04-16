from fastapi.testclient import TestClient
from hashlib import sha512
from datetime import date, timedelta

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
    hash_valid = sha512('haslo'.encode('utf8')).hexdigest()
    hash_invalid = sha512('inne_haslo'.encode('utf8')).hexdigest()
    hash_empty = sha512(''.encode('utf8')).hexdigest()
    response_valid = client.get(test_path, params={'password': 'haslo', 'password_hash': hash_valid})
    params_invalid = [
        {'password': 'haslo', 'password_hash': hash_invalid},
        {'password': 'haslo', 'password_hash': ''},
        {'password': 'haslo'},
        {'password': '', 'password_hash': hash_empty},
        {'password_hash': hash_empty},
        {'password_hash': ''},
        {}
    ]
    responses_invalid = [client.get(test_path, params=params) for params in params_invalid]

    assert response_valid.status_code == 204
    for response in responses_invalid:
        assert response.status_code == 401


def test_register():
    """Test patient registration - """
    test_path = '/register'
    payloads = [
        {"name": "Ryszard", "surname": "Kot"},
        {"name": "Krystyna", "surname": "Janda"},
        {"name": "Jan", "surname": "Nowak"}
    ]
    responses = [client.post(test_path, json=payload) for payload in payloads]
    id_counter = 1

    for response, payload in zip(responses, payloads):
        assert response.status_code == 201
        assert response.json() == {
            'name': payload['name'],
            'surname': payload['surname'],
            'id': id_counter,
            'register_date': str(date.today()),
            'vaccination_date': str(date.today() + timedelta(days=len(payload['name']+payload['surname'])))
        }
        id_counter += 1
