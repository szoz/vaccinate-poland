from fastapi import FastAPI, Request, Response
from hashlib import sha512

app = FastAPI()


@app.get('/')
def read_root():
    """Return dict with simple greeting."""
    return {'message': 'Hello world!'}


@app.post('/method', status_code=201)
@app.api_route('/method', methods=['GET', 'DELETE', 'PUT', 'OPTIONS'])
def get_method(request: Request):
    """Return dict with request method. Success status codes are handled by path decorators."""
    return {'method': request.method}


@app.get('/auth', status_code=204)
def validates_password(password: str = '', password_hash: str = ''):
    """Checks if provided password and password_hash match."""
    password_encoded = password.encode('utf8')
    if sha512(password_encoded).hexdigest() != password_hash:
        return Response(status_code=401)
