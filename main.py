from fastapi import FastAPI, Request, Response
from hashlib import sha512
from datetime import timedelta, date
import logging

from models import UnregisteredPatient, Patient

app = FastAPI()

app.patients = []
logger = logging.getLogger('uvicorn')


@app.get('/', tags=['helpers'])
def read_root():
    """Return simple message."""
    return {'message': 'Hello world!'}


@app.post('/method', status_code=201, tags=['helpers'])
@app.api_route('/method', methods=['GET', 'DELETE', 'PUT', 'OPTIONS'], tags=['helpers'])
def return_request_method(request: Request):
    """Return requests HTTP method."""
    return {'method': request.method}


@app.get('/auth', tags=['authentication'])
def validate_password(password: str = '', password_hash: str = ''):
    """Check if provided password and password_hash match."""
    password_encoded = password.encode('utf8')
    if not password or sha512(password_encoded).hexdigest() != password_hash:
        status_code = 401
    else:
        status_code = 204

    return Response(status_code=status_code)


@app.post('/register', status_code=201, response_model=Patient, tags=['register'])
def register_patient(unregistered_patient: UnregisteredPatient):
    """Register patient and returns saved record."""
    vaccination_delay = timedelta(days=len([letter for letter
                                            in unregistered_patient.name + unregistered_patient.surname
                                            if letter.isalpha()]))
    patient = Patient(name=unregistered_patient.name, surname=unregistered_patient.surname,
                      id=len(app.patients) + 1, register_date=date.today(),
                      vaccination_date=(date.today() + vaccination_delay))
    app.patients.append(patient)
    logger.info(f'Added {patient=}')
    return patient


@app.get('/patient/{patient_id}', response_model=Patient, tags=['patient'])
def get_patient(patient_id: int):
    """Reads patient record with given id."""
    if patient_id <= 0:
        return Response(status_code=400)
    elif patient_id > len(app.patients):
        return Response(status_code=404)
    else:
        return app.patients[patient_id - 1]
