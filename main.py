from fastapi import FastAPI, Request, Response, HTTPException, status, Path
from fastapi.responses import HTMLResponse
from hashlib import sha512
from datetime import timedelta, date

from models import UnregisteredPatient, Patient
from auth import router
from utils import logger

app = FastAPI()

app.patients = []
app.include_router(router)


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


@app.post('/register', status_code=status.HTTP_201_CREATED, response_model=Patient, tags=['patient'])
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


@app.get('/hello', tags=['helpers'])
def read_html():
    """Return simple HTML response."""
    text = f'<html><body><h1>Hello! Today date is {date.today()}</h1></body></html>'
    return HTMLResponse(text)
