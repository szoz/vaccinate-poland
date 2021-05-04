from fastapi import FastAPI, Request, Response, HTTPException, status, Depends, Query, Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from starlette.datastructures import URL
from hashlib import sha512
from datetime import timedelta, date
from logging import getLogger
from secrets import compare_digest
from os import environ
from functools import wraps

from models import UnregisteredPatient, Patient, FormatEnum

app = FastAPI()

app.patients = []
logger = getLogger('uvicorn')
security = HTTPBasic()


@app.get('/', tags=['helpers'])
def read_root():
    """Return simple message."""
    return {'message': 'Hello world!'}


@app.post('/method', status_code=status.HTTP_201_CREATED, tags=['helpers'])
@app.api_route('/method', methods=['GET', 'DELETE', 'PUT', 'OPTIONS'], tags=['helpers'])
def return_request_method(request: Request):
    """Return requests HTTP method."""
    return {'method': request.method}


@app.get('/auth', tags=['authentication'])
def validate_password(password: str = '', password_hash: str = ''):
    """Check if provided password and password_hash match."""
    password_encoded = password.encode('utf8')
    if not password or sha512(password_encoded).hexdigest() != password_hash:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Password and hash dont match')

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post('/register', status_code=status.HTTP_201_CREATED, response_model=Patient, tags=['register'])
def register_patient(unregistered_patient: UnregisteredPatient):
    """Register patient and returns saved record."""
    vaccination_delay = timedelta(days=len([letter for letter
                                            in unregistered_patient.name + unregistered_patient.surname
                                            if letter.isalpha()]))
    patient = Patient(name=unregistered_patient.name, surname=unregistered_patient.surname,
                      id=len(app.patients) + 1,
                      vaccination_date=(date.today() + vaccination_delay))
    app.patients.append(patient)
    logger.info(f'Added {patient=}')
    return patient


@app.get('/patient/{id}', response_model=Patient, tags=['patient'])
def get_patient(patient_id: int = Path(0, alias='id')):
    """Reads patient record with given id."""
    if patient_id <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Invalid ID')
    elif patient_id > len(app.patients):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Patient not found')

    return app.patients[patient_id - 1]


@app.get('/hello')
def read_html():
    """Return simple HTML response."""
    text = f'<html><body><h1>Hello! Today date is {date.today()}</h1></body></html>'
    return HTMLResponse(text)


def check_credentials(credentials: HTTPBasicCredentials):
    """Raises exception if given credentials not match (resistant to time attacks)."""
    correct_username = compare_digest(credentials.username, environ['USER_LOGIN'])
    correct_password = compare_digest(credentials.password, environ['USER_PASSWORD'])
    if not correct_username or not correct_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


@app.post('/login_session', tags=['authentication'])
def login_session(credentials: HTTPBasicCredentials = Depends(security)):
    """Create session if given credentials are valid."""
    logger.info(f'Login request with {credentials=}')
    check_credentials(credentials)
    response = Response(status_code=status.HTTP_201_CREATED)
    response.set_cookie('session_token', environ['SESSION_KEY'])
    return response


@app.post('/login_token', status_code=status.HTTP_201_CREATED, tags=['authentication'])
def login_token(credentials: HTTPBasicCredentials = Depends(security)):
    """Return token if given credentials are valid."""
    logger.info(f'Login request with {credentials=}')
    check_credentials(credentials)
    return {'token': environ['TOKEN_KEY']}


def format_message(message: str, message_format: FormatEnum):
    """Returns message in response based on given format."""
    if message_format.value == 'json':
        return JSONResponse({'message': f'{message}'})
    elif message_format.value == 'html':
        return HTMLResponse(f'<html><body><h1>{message}</h1></body></html>')

    return PlainTextResponse(f'{message}')


def session_required(func):
    """Raises exception if request argument in decorated view function doesn't contain valid session cookie."""

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        logger.info(f'Session validation {request.cookies=}')
        if not compare_digest(request.cookies.get('session_token', ''), environ['SESSION_KEY']):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        return func(request, *args, **kwargs)

    return wrapper


@app.get('/welcome_session', tags=['authentication'])
@session_required
def welcome_session(request: Request, message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Return welcome message to user based on given response format. Endpoint only available to users with valid
    session cookie - request argument is used in decorator."""

    return format_message('Welcome!', message_format)


def token_required(func):
    """Raises exception if token argument in decorated view function is invalid."""

    @wraps(func)
    def wrapper(token, *args, **kwargs):
        logger.info(f'Token validation {token=}')
        if not compare_digest(token, environ['TOKEN_KEY']):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        return func(token, *args, **kwargs)

    return wrapper


@app.get('/welcome_token', tags=['authentication'])
@token_required
def welcome_token(token: str = '', message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Return welcome message to user based on given response format. Endpoint only available to users with valid token
     - token argument is used in decorator."""

    return format_message('Welcome!', message_format)


@app.delete('/logout_session', tags=['authentication'])
@session_required
def logout_session(request: Request):
    """Logs out user by removing cookie session. Endpoint only available to users with valid session cookie - request
    argument is used also in decorator."""
    redirect_path = '/logged_out'
    if request.query_params:
        redirect_path += f'?{request.query_params}'
    response = RedirectResponse(URL(redirect_path), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('session_token')

    return response


@app.delete('/logout_token', tags=['authentication'])
@token_required
def logout_session(token: str = '', message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Logs out user by removing token session. Endpoint only available to users with valid token - token argument
    is used in decorator."""
    redirect_path = '/logged_out'
    if message_format != FormatEnum.txt:
        redirect_path += f'?format={message_format}'
    response = RedirectResponse(URL(redirect_path), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('session_token')

    return response


@app.get('/logged_out', tags=['authentication'])
def logout(message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Return message to user after log out."""
    return format_message('Logged out!', message_format)
