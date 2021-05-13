from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from logging import getLogger
from secrets import compare_digest, token_hex
from os import environ

from models import FormatEnum


logger = getLogger('uvicorn')


def check_credentials(credentials: HTTPBasicCredentials):
    """Raises exception if given credentials not match (resistant to time attacks)."""
    correct_username = compare_digest(credentials.username, environ['USER_LOGIN'])
    correct_password = compare_digest(credentials.password, environ['USER_PASSWORD'])
    if not correct_username or not correct_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


def create_login_key():
    """Return string with random 16-byte value."""
    return token_hex(16)


def format_message(message: str, message_format: FormatEnum):
    """Returns message in response based on given format."""
    if message_format.value == 'json':
        return JSONResponse({'message': f'{message}'})
    elif message_format.value == 'html':
        return HTMLResponse(f'<html><body><h1>{message}</h1></body></html>')

    return PlainTextResponse(f'{message}')
