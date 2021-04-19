from pydantic import BaseModel
from datetime import date


class UnregisteredPatient(BaseModel):
    """Patient waiting to be registered."""
    name: str
    surname: str


class Patient(UnregisteredPatient):
    """Patient registered for vaccination."""
    id: int = None
    register_date: date = None
    vaccination_date: date = None
