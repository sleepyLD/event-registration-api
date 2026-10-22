"""All slot changes lock the event first, in the same transaction."""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Event, User, Registration


class BusinessError(Exception):
    def __init__(self, code: str, status: int = 404):
        self.code = code
        self.status = status


def get_event(session: Session, event_id: int, *, lock: bool = False) -> Event:
    stmt = select(Event).where(Event.id == event_id)
    if lock:
        stmt = stmt.with_for_update()
    event = session.scalar(stmt)
    if event is None:
        raise BusinessError('EVENT_NOT_FOUND')
    return event


def get_active(session: Session, event_id: int, user_id: int):
    return session.scalar(select(Registration).where(
        Registration.event_id == event_id,
        Registration.user_id == user_id,
        Registration.status == 'active',
    ))


def change_registration(session: Session, event_id: int, user_id: int, *, cancel: bool = False):
    # Caller owns begin/commit/rollback. PostgreSQL READ COMMITTED is assumed.
    event = get_event(session, event_id, lock=True)
    if session.get(User, user_id) is None:
        raise BusinessError('USER_NOT_FOUND')
    active = get_active(session, event_id, user_id)
    if cancel:
        if active is None:
            raise BusinessError('REGISTRATION_NOT_FOUND')
        active.status = 'cancelled'
        active.cancelled_at = datetime.now(timezone.utc)
        event.remaining_slots += 1
        session.flush()
        return None
    if active is not None:
        raise BusinessError('ALREADY_REGISTERED', 409)
    if event.remaining_slots == 0:
        raise BusinessError('EVENT_FULL', 409)
    event.remaining_slots -= 1
    registration = Registration(event_id=event_id, user_id=user_id, status='active')
    session.add(registration)
    session.flush()
    return registration
