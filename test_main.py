import pytest
from fastapi.testclient import TestClient
from hashlib import sha512
from datetime import date, timedelta
from os import environ

from main import app


@pytest.fixture()
def client():
    """Prepare FastAPI test client."""
    return TestClient(app)


@pytest.fixture()
def patient_payloads():
    """Prepare Patient payloads with expected attributes."""
    patients = [{'name': 'Ryszard', 'surname': 'Kot'},
                {'name': 'Krystyna', 'surname': 'Janda'},
                {'name': 'Jan', 'surname': 'Nowak2'},
                {'name': 'Jan Stefan', 'surname': 'Nowak'},
                {'name': 'Jan', 'surname': 'Nowak!@#$%^&*()_+/'}]
    delays = [10, 13, 8, 14, 8]
    return {'patients': patients, 'delays': delays}


def test_root(client):
    """Test '/' endpoint basic response."""
    response = client.get('/')

    assert response.status_code == 200
    assert response.json() == {'message': 'Hello world!'}


def test_method(client):
    """Test status codes and returned methods in '/method' responses."""
    test_path = '/method'
    methods_to_status = {'GET': 200,
                         'POST': 201,
                         'DELETE': 200,
                         'PUT': 200,
                         'OPTIONS': 200}
    responses = [client.request(method, test_path) for method in methods_to_status.keys()]

    for case, response in zip(methods_to_status.items(), responses):
        assert response.status_code == case[1]
        assert response.json().get('method') == case[0]


def test_auth(client):
    """Test status codes in '/auth' endpoint responses."""
    test_path = '/auth'
    hash_valid = sha512('haslo'.encode('utf8')).hexdigest()
    hash_invalid = sha512('inne_haslo'.encode('utf8')).hexdigest()
    hash_empty = sha512(''.encode('utf8')).hexdigest()
    response_valid = client.get(test_path, params={'password': 'haslo', 'password_hash': hash_valid})
    params_invalid = [{'password': 'haslo', 'password_hash': hash_invalid},
                      {'password': 'haslo', 'password_hash': ''},
                      {'password': 'haslo'},
                      {'password': '', 'password_hash': hash_empty},
                      {'password_hash': hash_empty},
                      {'password_hash': ''},
                      {}]
    responses_invalid = [client.get(test_path, params=params) for params in params_invalid]

    assert response_valid.status_code == 204
    for response in responses_invalid:
        assert response.status_code == 401


def test_register(client, patient_payloads):
    """Test adding patient records in '/register' endpoint."""
    test_path = '/register'
    responses = [client.post(test_path, json=payload) for payload in patient_payloads['patients']]
    id_counter = 1

    for response, payload, delay in zip(responses, patient_payloads['patients'], patient_payloads['delays']):
        assert response.status_code == 201
        patient = response.json()
        # noinspection PyTypeChecker
        assert patient == {'name': payload['name'],
                           'surname': payload['surname'],
                           'id': id_counter,
                           'register_date': str(date.today()),
                           'vaccination_date': str(date.today() + timedelta(days=delay))}
        id_counter += 1


def test_patient(client, patient_payloads):
    """Test getting patient records in '/patient' endpoint based on data added in test_register test case."""
    test_path = '/patient/{}'
    patient_count = len(patient_payloads['patients'])
    responses_valid = [client.get(test_path.format(pid + 1)) for pid in range(patient_count)]
    responses_invalid = {400: client.get(test_path.format(-1)),
                         404: client.get(test_path.format(1000))}

    for response, payload in zip(responses_valid, patient_payloads['patients']):
        assert response.status_code == 200
        assert response.json().items() >= payload.items()
    for code, response in responses_invalid.items():
        assert response.status_code == code


def test_html(client):
    """Test endpoint '/hello' with simple HTML response."""
    test_path = '/hello'
    expected_text = f'<h1>Hello! Today date is {date.today()}</h1>'

    response = client.get(test_path)
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert expected_text in response.text


def test_login_session(client):
    """Test cookie session in '/login_session' endpoint."""
    test_path = '/login_session'
    credentials_invalid = ('admin', '123456')
    credentials_valid = (environ['USER_LOGIN'], environ['USER_PASSWORD'])

    response_invalid = client.post(test_path, auth=credentials_invalid)
    response_valid = client.post(test_path, auth=credentials_valid)
    assert response_invalid.status_code == 401
    assert response_valid.status_code == 201
    assert ['session_token'] == response_valid.cookies.keys()


def test_login_token(client):
    """Test '/login_token' response."""
    test_path = '/login_token'
    credentials_invalid = ('admin', '123456')
    credentials_valid = (environ['USER_LOGIN'], environ['USER_PASSWORD'])

    response_invalid = client.post(test_path, auth=credentials_invalid)
    response_valid = client.post(test_path, auth=credentials_valid)
    assert response_invalid.status_code == 401
    assert response_valid.status_code == 201
    assert ['token'] == list(response_valid.json().keys())
