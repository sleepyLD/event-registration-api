"""Database schema shared by the application and Alembic."""
from datetime import datetime
from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, DateTime, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("btrim(name) <> ''", name='ck_users_name'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    __tablename__ = 'events'
    __table_args__ = (
        CheckConstraint("btrim(title) <> ''", name='ck_events_title'),
        CheckConstraint('capacity BETWEEN 1 AND 10000', name='ck_events_capacity'),
        CheckConstraint('remaining_slots BETWEEN 0 AND capacity', name='ck_events_slots'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    capacity: Mapped[int]
    remaining_slots: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Registration(Base):
    __tablename__ = 'registrations'
    __table_args__ = (
        CheckConstraint("status IN ('active', 'cancelled')", name='ck_registration_status'),
        CheckConstraint("(status = 'active' AND cancelled_at IS NULL) OR (status = 'cancelled' AND cancelled_at IS NOT NULL)", name='ck_registration_cancelled_at'),
        Index('uq_active_registration', 'event_id', 'user_id', unique=True, postgresql_where=text("status = 'active'")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id', ondelete='RESTRICT'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'))
    status: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
