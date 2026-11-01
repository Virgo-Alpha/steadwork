"""SQLAlchemy engine, generic CRUD repositories, and domain-store adapter."""

from pathlib import Path

from sqlalchemy import delete, event, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from .database import DatabaseConfigurationError, get_database_url
from .models import Application, Company, Job, Membership, Notification, User
from .orm import (
    ApplicationRecord, Base, CompanyRecord, JobRecord, MembershipRecord,
    NotificationRecord, ProfileRecord, SavedJobRecord, UserRecord,
)


def create_database(url: str | None = None):
    """Create SQLite engine/session factory and ensure the current schema exists."""
    url = get_database_url({"DATABASE_URL": url}) if url is not None else get_database_url()
    parsed = make_url(url)
    if parsed.drivername not in {"sqlite", "sqlite+pysqlite"}:
        raise DatabaseConfigurationError("Only SQLite DATABASE_URL values are supported by this backend.")
    if parsed.database and parsed.database != ":memory:" and not parsed.database.startswith("file:"):
        Path(parsed.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


class Repository:
    """Small generic CRUD repository for one mapped SQLAlchemy entity."""

    def __init__(self, session: Session, model):
        self.session = session
        self.model = model
        self.primary_key_names = [column.key for column in model.__mapper__.primary_key]

    def get(self, key):
        identity = (key,) if len(self.primary_key_names) == 1 and not isinstance(key, tuple) else key
        return self.session.get(self.model, identity)

    def list(self):
        return list(self.session.scalars(select(self.model)).all())

    def save(self, record):
        result = self.session.merge(record)
        self.session.flush()
        return result

    def delete(self, key):
        record = self.get(key)
        if record is None:
            return False
        self.session.delete(record)
        self.session.flush()
        return True


class SQLAlchemyStoreRepository:
    """Translate the route layer's dataclass store to normalized ORM rows."""

    def __init__(self, session: Session):
        self.session = session

    def load(self):
        if self.session.scalar(select(UserRecord.id).limit(1)) is None:
            from .store import _seed

            self.replace(_seed())
            self.session.flush()
        users = [User(row.id, row.email, row.role, row.password_hash) for row in self.session.scalars(select(UserRecord).order_by(UserRecord.position, UserRecord.id)).all()]
        companies = [Company(row.id, row.name, row.description, row.website, row.logo, row.accent) for row in self.session.scalars(select(CompanyRecord).order_by(CompanyRecord.position, CompanyRecord.id)).all()]
        jobs = [
            Job(row.id, row.company_id, row.title, row.description, row.location, row.salary_min, row.salary_max,
                row.currency, row.remote_policy, row.job_type, row.experience_level, row.skills, row.responsibilities,
                row.qualifications, row.benefits, row.application_method, row.external_apply_url, row.status,
                row.posted_at, row.deadline, row.application_count)
            for row in self.session.scalars(select(JobRecord).order_by(JobRecord.position, JobRecord.id)).all()
        ]
        applications = [
            Application(row.id, row.job_id, row.candidate_id, row.status, row.candidate_name, row.candidate_email,
                        row.cv_name, row.cover_letter, row.created_at)
            for row in self.session.scalars(select(ApplicationRecord).order_by(ApplicationRecord.position, ApplicationRecord.id)).all()
        ]
        profiles = {row.user_id: dict(row.data) for row in self.session.scalars(select(ProfileRecord)).all()}
        saved_jobs = {}
        for row in self.session.scalars(select(SavedJobRecord)).all():
            saved_jobs.setdefault(row.user_id, set()).add(row.job_id)
        memberships = [Membership(row.user_id, row.company_id, row.role) for row in self.session.scalars(select(MembershipRecord).order_by(MembershipRecord.position, MembershipRecord.user_id, MembershipRecord.company_id)).all()]
        notifications = [
            Notification(row.id, row.user_id, row.title, row.body, row.read_at, row.created_at)
            for row in self.session.scalars(select(NotificationRecord).order_by(NotificationRecord.position, NotificationRecord.id)).all()
        ]
        from .store import InMemoryStore

        return InMemoryStore(users, companies, jobs, applications, profiles, saved_jobs, memberships, notifications)

    def replace(self, store):
        """Atomically mirror a domain-store snapshot, including removals."""
        models_in_delete_order = [
            NotificationRecord, SavedJobRecord, MembershipRecord, ProfileRecord,
            ApplicationRecord, JobRecord, CompanyRecord, UserRecord,
        ]
        for model in models_in_delete_order:
            self.session.execute(delete(model))
        self.session.flush()
        for position, item in enumerate(store.users):
            self.session.add(UserRecord(id=item.id, email=item.email, role=item.role, password_hash=item.password_hash, position=position))
        for position, item in enumerate(store.companies):
            self.session.add(CompanyRecord(id=item.id, name=item.name, description=item.description, website=item.website, logo=item.logo, accent=item.accent, position=position))
        self.session.flush()
        for position, item in enumerate(store.jobs):
            self.session.add(JobRecord(
                id=item.id, company_id=item.company_id, title=item.title, description=item.description, location=item.location,
                salary_min=item.salary_min, salary_max=item.salary_max, currency=item.currency, remote_policy=item.remote_policy,
                job_type=item.job_type, experience_level=item.experience_level, skills=item.skills or [],
                responsibilities=item.responsibilities or [], qualifications=item.qualifications or [], benefits=item.benefits or [],
                application_method=item.application_method, external_apply_url=item.external_apply_url, status=item.status,
                posted_at=item.posted_at, deadline=item.deadline, application_count=item.application_count, position=position,
            ))
        self.session.flush()
        for position, item in enumerate(store.applications):
            self.session.add(ApplicationRecord(
                id=item.id, job_id=item.job_id, candidate_id=item.candidate_id, status=item.status,
                candidate_name=item.candidate_name, candidate_email=item.candidate_email, cv_name=item.cv_name,
                cover_letter=item.cover_letter, created_at=item.created_at, position=position,
            ))
        for user_id, data in store.profiles.items():
            self.session.add(ProfileRecord(user_id=user_id, data=dict(data)))
        for user_id, job_ids in store.saved_jobs.items():
            for job_id in job_ids:
                self.session.add(SavedJobRecord(user_id=user_id, job_id=job_id))
        for position, item in enumerate(store.memberships):
            self.session.add(MembershipRecord(user_id=item.user_id, company_id=item.company_id, role=item.role, position=position))
        for position, item in enumerate(store.notifications):
            self.session.add(NotificationRecord(
                id=item.id, user_id=item.user_id, title=item.title, body=item.body,
                read_at=item.read_at, created_at=item.created_at, position=position,
            ))
        self.session.flush()

