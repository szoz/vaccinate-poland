from fastapi import APIRouter, Request, Response, HTTPException, status, Depends, Query, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from starlette.datastructures import URL
from collections import deque
from functools import wraps

from models import FormatEnum
from utils import logger, check_credentials, create_login_key, format_message

router = APIRouter(tags=['authentication'])
security = HTTPBasic()

router.session_keys = deque([], maxlen=3)
router.token_keys = deque([], maxlen=3)


def session_required(func):
    """Raises exception if request argument in decorated view function doesn't contain valid session cookie."""

    @wraps(func)
    def wrapper(session_token, **kwargs):
        logger.info(f'Session validation {session_token=}')
        if session_token not in router.session_keys:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        return func(session_token, **kwargs)

    return wrapper


def token_required(func):
    """Raises exception if token argument in decorated view function is invalid."""

    @wraps(func)
    def wrapper(token, **kwargs):
        logger.info(f'Token validation {token=}')
        if token not in router.token_keys:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        return func(token, **kwargs)

    return wrapper


@router.post('/login_session')
def login_session(credentials: HTTPBasicCredentials = Depends(security)):
    """Create session if given credentials are valid."""
    logger.info(f'Login request with {credentials=}')
    check_credentials(credentials)
    response = Response(status_code=status.HTTP_201_CREATED)
    session = create_login_key()
    response.set_cookie('session_token', session)
    router.session_keys.append(session)
    return response


@router.post('/login_token', status_code=status.HTTP_201_CREATED)
def login_token(credentials: HTTPBasicCredentials = Depends(security)):
    """Return token if given credentials are valid."""
    logger.info(f'Login request with {credentials=}')
    check_credentials(credentials)
    token = create_login_key()
    router.token_keys.append(token)
    return {'token': token}


@router.get('/welcome_session')
@session_required
def welcome_session(session_token: str = Cookie(''),
                    message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Return welcome message to user based on given response format. Endpoint only available to users with valid
    session cookie - request argument is used in decorator."""

    return format_message('Welcome!', message_format)


@router.get('/welcome_token')
@token_required
def welcome_token(token: str = '', message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Return welcome message to user based on given response format. Endpoint only available to users with valid token
     - token argument is used in decorator."""

    return format_message('Welcome!', message_format)


@router.delete('/logout_session')
@session_required
def logout_session(session_token: str = Cookie(''), request: Request = ...):
    """Logs out user by removing cookie session. Endpoint only available to users with valid session cookie - request
    argument is used also in decorator."""
    redirect_path = '/logged_out'
    if request.query_params:
        redirect_path += f'?{request.query_params}'
    response = RedirectResponse(URL(redirect_path), status_code=status.HTTP_303_SEE_OTHER)
    session = request.cookies['session_token']
    response.delete_cookie('session_token')
    router.session_keys.remove(session)

    return response


@router.delete('/logout_token')
@token_required
def logout_session(token: str = '', message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Logs out user by removing token session. Endpoint only available to users with valid token - token argument
    is used in decorator."""
    redirect_path = '/logged_out'
    if message_format != FormatEnum.txt:
        redirect_path += f'?format={message_format}'
    response = RedirectResponse(URL(redirect_path), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('session_token')
    router.token_keys.remove(token)

    return response


@router.get('/logged_out')
def logout(message_format: FormatEnum = Query(FormatEnum.txt, alias='format')):
    """Return message to user after log out."""
    return format_message('Logged out!', message_format)
