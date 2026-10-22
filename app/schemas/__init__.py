from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class UserCreate(Input):
    name: Name


class EventCreate(Input):
    title: Name
    capacity: Annotated[int, Field(strict=True, ge=1, le=10000)]


class RegistrationCreate(Input):
    user_id: PositiveInt


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserRead(Output):
    id: int
    name: str
    created_at: datetime


class EventRead(Output):
    id: int
    title: str
    capacity: int
    remaining_slots: int
    created_at: datetime


class RegistrationRead(Output):
    id: int
    event_id: int
    user_id: int
    status: Literal['active', 'cancelled']
    created_at: datetime
    cancelled_at: datetime | None


class ErrorRead(BaseModel):
    code: str
    message: str


class HealthRead(BaseModel):
    status: Literal['ok'] = 'ok'
    database: Literal['ok'] = 'ok'
