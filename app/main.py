from contextlib import asynccontextmanager
import logging
from typing import Annotated
from fastapi import FastAPI, Request, Path, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.db.connection import build_engine
from app.models import User, Event, Registration
from app.schemas import UserCreate, UserRead, EventCreate, EventRead, RegistrationCreate, RegistrationRead, HealthRead, ErrorRead
from app.services.registrations import BusinessError, get_event, change_registration

logger = logging.getLogger(__name__)
ID = Annotated[int, Path(gt=0)]
ERRORS = {code: {'model': ErrorRead} for code in (404, 409, 422, 500)}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = build_engine()
    try:
        yield
    finally:
        app.state.engine.dispose()


app = FastAPI(title='Event Registration API', version='0.1.0', lifespan=lifespan,
              description='Small PostgreSQL-backed portfolio demo. No authentication.')


@app.exception_handler(BusinessError)
async def business_error(request: Request, exc: BusinessError):
    return JSONResponse(status_code=exc.status, content={'code': exc.code, 'message': exc.code.replace('_', ' ').capitalize()})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    details = [{'loc': list(e['loc']), 'type': e['type'], 'message': e['msg']} for e in exc.errors()]
    return JSONResponse(status_code=422, content={'code': 'VALIDATION_ERROR', 'message': 'Invalid request', 'details': details})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.error('Unexpected server error: %s', type(exc).__name__)
    return JSONResponse(status_code=500, content={'code': 'INTERNAL_ERROR', 'message': 'Unexpected server error'})


@app.get('/health', response_model=HealthRead, responses={503: {'model': ErrorRead}})
def health(request: Request):
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
    except SQLAlchemyError as exc:
        logger.warning('Database health check failed: %s', type(exc).__name__)
        return JSONResponse(status_code=503, content={'code': 'DATABASE_UNAVAILABLE', 'message': 'Database unavailable'})
    return HealthRead()


@app.post('/users', status_code=201, response_model=UserRead, responses=ERRORS)
def create_user(body: UserCreate, request: Request):
    with Session(request.app.state.engine) as session, session.begin():
        user = User(name=body.name)
        session.add(user)
        session.flush()
        result = UserRead.model_validate(user)
    return result


@app.post('/events', status_code=201, response_model=EventRead, responses=ERRORS)
def create_event(body: EventCreate, request: Request):
    with Session(request.app.state.engine) as session, session.begin():
        event = Event(title=body.title, capacity=body.capacity, remaining_slots=body.capacity)
        session.add(event)
        session.flush()
        result = EventRead.model_validate(event)
    return result


@app.get('/events', response_model=list[EventRead])
def list_events(request: Request):
    with Session(request.app.state.engine) as session:
        return [EventRead.model_validate(e) for e in session.scalars(select(Event).order_by(Event.id))]


@app.get('/events/{event_id}', response_model=EventRead, responses=ERRORS)
def read_event(event_id: ID, request: Request):
    with Session(request.app.state.engine) as session:
        return EventRead.model_validate(get_event(session, event_id))


@app.post('/events/{event_id}/registrations', status_code=201, response_model=RegistrationRead, responses=ERRORS)
def register(event_id: ID, body: RegistrationCreate, request: Request):
    with Session(request.app.state.engine) as session, session.begin():
        registration = change_registration(session, event_id, body.user_id)
        result = RegistrationRead.model_validate(registration)
    return result


@app.get('/events/{event_id}/registrations', response_model=list[RegistrationRead], responses=ERRORS)
def list_registrations(event_id: ID, request: Request):
    with Session(request.app.state.engine) as session:
        get_event(session, event_id)
        rows = session.scalars(select(Registration).where(Registration.event_id == event_id, Registration.status == 'active').order_by(Registration.id))
        return [RegistrationRead.model_validate(r) for r in rows]


@app.delete('/events/{event_id}/registrations/{user_id}', status_code=204, responses=ERRORS)
def cancel_registration(event_id: ID, user_id: ID, request: Request):
    with Session(request.app.state.engine) as session, session.begin():
        change_registration(session, event_id, user_id, cancel=True)
    return Response(status_code=204)
