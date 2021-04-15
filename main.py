from fastapi import FastAPI, Request

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
