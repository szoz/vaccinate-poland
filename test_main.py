import pytest
from fastapi.testclient import TestClient
from hashlib import sha512
from datetime import date, timedelta
from os import environ

from main import app


@pytest.fixture
def client():
    """Prepare FastAPI test client."""
    return TestClient(app)


@pytest.fixture
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
    params_invalid = [{'password': 'haslo', 'password_hash': hash_invalid},
                      {'password': 'haslo', 'password_hash': ''},
                      {'password': 'haslo'},
                      {'password': '', 'password_hash': hash_empty},
                      {'password_hash': hash_empty},
                      {'password_hash': ''},
                      {}]

    response_valid = client.get(test_path, params={'password': 'haslo', 'password_hash': hash_valid})
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


@pytest.fixture
def credentials():
    """Return tuple with user login and password."""
    return environ['USER_LOGIN'], environ['USER_PASSWORD']


def test_login_session(client, credentials):
    """Test session receiving in '/login_session' endpoint."""
    test_path = '/login_session'
    credentials_invalid = ('admin', '123456')

    response_invalid = client.post(test_path, auth=credentials_invalid)
    response_valid = client.post(test_path, auth=credentials)

    assert response_invalid.status_code == 401
    assert response_valid.status_code == 201
    assert response_valid.cookies.get('session_token')


def test_login_token(client, credentials):
    """Test token receiving in '/login_token' endpoint."""
    test_path = '/login_token'
    credentials_invalid = ('admin', '123456')

    response_invalid = client.post(test_path, auth=credentials_invalid)
    response_valid = client.post(test_path, auth=credentials)

    assert response_invalid.status_code == 401
    assert response_valid.status_code == 201
    assert response_valid.json().get('token')


def test_welcome_session(client, credentials):
    """Test authentication in '/welcome_session' endpoint."""
    login_path = '/login_session'
    test_path = '/welcome_session'
    session = client.post(login_path, auth=credentials).cookies

    response_invalid = client.get(test_path, cookies={'session_token': 'invalid'})
    response_blank = client.get(test_path, cookies={'session_token': ''})
    response_valid_text = client.get(test_path, cookies=session)
    response_valid_html = client.get(test_path, cookies=session, params={'format': 'html'})
    response_valid_json = client.get(test_path, cookies=session, params={'format': 'json'})

    assert response_invalid.status_code == 401
    assert response_blank.status_code == 401

    assert response_valid_text.status_code == 200
    assert response_valid_text.headers['content-type'].startswith('text/plain')
    assert response_valid_text.text == 'Welcome!'

    assert response_valid_json.status_code == 200
    assert response_valid_json.headers['content-type'].startswith('application/json')
    assert response_valid_json.json() == {'message': 'Welcome!'}

    assert response_valid_html.status_code == 200
    assert response_valid_html.headers['content-type'].startswith('text/html')
    assert '<h1>Welcome!</h1>' in response_valid_html.text


def test_welcome_token(client, credentials):
    """Test authentication in '/welcome_token' endpoint."""
    login_path = '/login_token'
    test_path = '/welcome_token'
    token = client.post(login_path, auth=credentials).json()['token']

    response_invalid = client.get(test_path, params={'token': 'invalid'})
    response_blank = client.get(test_path, params={'token': ''})
    response_valid_text = client.get(test_path, params={'token': token})
    response_valid_html = client.get(test_path, params={'token': token, 'format': 'html'})
    response_valid_json = client.get(test_path, params={'token': token, 'format': 'json'})

    assert response_invalid.status_code == 401
    assert response_blank.status_code == 401

    assert response_valid_text.status_code == 200
    assert response_valid_text.headers['content-type'].startswith('text/plain')
    assert response_valid_text.text == 'Welcome!'

    assert response_valid_json.status_code == 200
    assert response_valid_json.headers['content-type'].startswith('application/json')
    assert response_valid_json.json() == {'message': 'Welcome!'}

    assert response_valid_html.status_code == 200
    assert response_valid_html.headers['content-type'].startswith('text/html')
    assert '<h1>Welcome!</h1>' in response_valid_html.text


def test_logout_session(client, credentials):
    """Test authentication termination in '/logout_session' endpoint."""
    login_path = '/login_session'
    test_path = '/logout_session'

    client.post(login_path, auth=credentials)  # Initialize session in app cache
    response_invalid = client.delete(test_path, cookies={'session_token': 'invalid'})
    response_blank = client.delete(test_path, cookies={'session_token': ''})
    responses_valid, responses_redirected = [], []
    params_valid = [{}, {'format': 'html'}, {'format': 'json'}]
    for params in params_valid:
        session = client.post(login_path, auth=credentials).cookies
        response = client.delete(test_path, cookies=session, params=params)
        responses_valid.append(response)
        responses_redirected.append(client.send(response.next))
    session = client.post(login_path, auth=credentials).cookies
    client.delete(test_path, cookies=session)
    response_duplicate = client.delete(test_path, cookies=session)

    assert response_invalid.status_code == 401
    assert response_blank.status_code == 401
    assert response_duplicate.status_code == 401

    for rv, rr in zip(responses_valid, responses_redirected):
        assert rv.status_code in [302, 303]
        assert rv.cookies.get_dict() == {}
        assert rr.status_code == 200
        assert '/logged_out' in rr.url
        assert 'Logged out!' in rr.text


def test_logout_token(client, credentials):
    """Test authentication termination in '/logout_token' endpoint."""
    login_path = '/login_token'
    test_path = '/logout_token'

    client.post(login_path, auth=credentials)  # Initialize session in app cache
    response_invalid = client.delete(test_path, params={'token': 'invalid'})
    response_blank = client.delete(test_path, params={'token': ''})
    responses_valid, responses_redirected = [], []
    params_valid = [{}, {'format': 'html'}, {'format': 'json'}]
    for params in params_valid:
        token = client.post(login_path, auth=credentials).json()['token']
        response = client.delete(test_path, params={'token': token, **params})
        responses_valid.append(response)
        responses_redirected.append(client.send(response.next))
    token = client.post(login_path, auth=credentials).cookies
    client.delete(test_path, params={'token': token})
    response_duplicate = client.delete(test_path, params={'token': token})

    assert response_invalid.status_code == 401
    assert response_blank.status_code == 401
    assert response_duplicate.status_code == 401

    for rv, rr in zip(responses_valid, responses_redirected):
        assert rv.status_code in [302, 303]
        assert rv.cookies.get_dict() == {}
        assert rr.status_code == 200
        assert '/logged_out' in rr.url
        assert 'Logged out!' in rr.text


def test_multiple_login(client, credentials):
    """Tests caching 3 last sessions in '/logout_session' and 3 last tokens in '/logout_token' endpoint."""
    login_session_path = '/login_session'
    login_token_path = '/login_token'
    welcome_session_path = '/welcome_session'
    welcome_token_path = '/welcome_token'

    sessions = [client.post(login_session_path, auth=credentials).cookies for _ in range(4)]
    tokens = [client.post(login_token_path, auth=credentials).json()['token'] for _ in range(4)]
    responses_session = [client.get(welcome_session_path, cookies=session) for session in sessions]
    responses_token = [client.get(welcome_token_path, params={'token': token}) for token in tokens]

    assert responses_session[0].status_code == 401
    assert responses_token[0].status_code == 401
    for response in responses_session[1:]:
        assert response.status_code == 200
    for response in responses_token[1:]:
        assert response.status_code == 200
