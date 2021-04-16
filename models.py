from pydantic import BaseModel
from datetime import date


class Patient(BaseModel):
    """Patient registered for vaccination."""
    name: str
    surname: str
    id: int = None
    register_date = date.today()
    vaccination_date: date = None
