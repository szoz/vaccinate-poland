from pydantic import BaseModel
from datetime import date
from enum import Enum


class UnregisteredPatient(BaseModel):
    """Patient waiting to be registered."""
    name: str
    surname: str


class Patient(UnregisteredPatient):
    """Patient registered for vaccination."""
    id: int = None
    register_date: date = date.today()
    vaccination_date: date = None


class FormatEnum(str, Enum):
    """HTTP response message format enumerator."""
    txt = 'txt'
    html = 'html'
    json = 'json'
