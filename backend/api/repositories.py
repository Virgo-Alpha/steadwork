"""SQLAlchemy engine, generic CRUD repositories, and domain-store adapter."""

from pathlib import Path

from sqlalchemy import delete, event, select
from sqlalchemy.engine import make_url
from sqlalchemy import inspect
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from .database import DatabaseConfigurationError, get_database_url
from .models import ActivityEvent, Application, Company, Job, Membership, Notification, User
from .orm import (
    ActivityEventRecord, ApplicationRecord, Base, CompanyRecord, JobRecord, MembershipRecord,
    NotificationRecord, ProfileRecord, SavedJobRecord, UserRecord,
)


def create_database(url: str | None = None):
    """Create an engine only when Alembic has initialized the current schema."""
    url = get_database_url({"DATABASE_URL": url}) if url is not None else get_database_url()
    parsed = make_url(url)
    if parsed.drivername not in {"sqlite", "sqlite+pysqlite", "postgresql", "postgresql+psycopg"}:
        raise DatabaseConfigurationError("DATABASE_URL must use SQLite or PostgreSQL.")
    is_sqlite = parsed.drivername in {"sqlite", "sqlite+pysqlite"}
    if is_sqlite and parsed.database and parsed.database != ":memory:" and not parsed.database.startswith("file:"):
        Path(parsed.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30} if is_sqlite else {})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        if engine.dialect.name != "sqlite":
            return
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    config_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    config = Config(str(config_path))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["database_url"] = url
    expected_head = ScriptDirectory.from_config(config).get_current_head()
    try:
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            if "alembic_version" not in tables:
                current_revision = None
            else:
                current_revision = MigrationContext.configure(connection).get_current_revision()
        missing_tables = set(Base.metadata.tables) - tables
        if current_revision != expected_head or missing_tables:
            details = f" Missing tables: {', '.join(sorted(missing_tables))}." if missing_tables else ""
            raise DatabaseConfigurationError(
                "Database schema is not at the current Alembic revision; run `uv run alembic upgrade head`."
                + details
            )
    except Exception:
        engine.dispose()
        raise
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
        else:
            # Add the expanded demo catalog once to databases created with the
            # original two-job seed. Never replace or overwrite existing rows.
            core_ids = {"job-platform", "job-design"}
            extra_ids = {
                "job-security", "job-analytics", "job-infrastructure",
                "job-research", "job-devrel", "job-accessibility",
            }
            existing_ids = set(self.session.scalars(select(JobRecord.id)).all())
            if extra_ids & existing_ids:
                # These fixed sample postings were originally attached to the
                # recruiter fixture's company; keep that account's fixture
                # focused on its original managed job.
                misowned_ids = set(self.session.scalars(
                    select(JobRecord.id).where(
                        JobRecord.id.in_(extra_ids),
                        JobRecord.company_id == "company-acme",
                    )
                ).all())
                if misowned_ids:
                    self.session.query(JobRecord).filter(
                        JobRecord.id.in_(misowned_ids),
                    ).update({JobRecord.company_id: "company-orbit"}, synchronize_session=False)
            if core_ids <= existing_ids and not (extra_ids & existing_ids):
                from .store import _seed

                seed_jobs = _seed().jobs
                next_position = max(
                    self.session.scalars(select(JobRecord.position)).all(),
                    default=-1,
                ) + 1
                for item in seed_jobs:
                    if item.id in extra_ids:
                        self.session.add(JobRecord(
                            id=item.id, company_id=item.company_id, title=item.title,
                            description=item.description, location=item.location,
                            salary_min=item.salary_min, salary_max=item.salary_max,
                            currency=item.currency, remote_policy=item.remote_policy,
                            job_type=item.job_type, experience_level=item.experience_level,
                            skills=item.skills or [], responsibilities=item.responsibilities or [],
                            qualifications=item.qualifications or [], benefits=item.benefits or [],
                            application_method=item.application_method,
                            external_apply_url=item.external_apply_url, status=item.status,
                            posted_at=item.posted_at, deadline=item.deadline,
                            application_count=item.application_count, position=next_position,
                        ))
                        next_position += 1
                self.session.flush()
            from .store import _demo_observability_seed_enabled, _seed

            if _demo_observability_seed_enabled() and self.session.scalar(
                select(ActivityEventRecord.id).where(ActivityEventRecord.origin == "demo").limit(1)
            ) is None:
                demo_seed = _seed()
                for item in demo_seed.activity_events:
                    self.session.add(ActivityEventRecord(
                        id=item.id, event_type=item.event_type, occurred_at=item.occurred_at,
                        actor_user_id=item.actor_user_id, actor_role=item.actor_role,
                        subject_type=item.subject_type, subject_id=item.subject_id,
                        application_method=item.application_method, origin=item.origin,
                    ))
                if (
                    self.session.get(UserRecord, "user-candidate") is not None
                    and self.session.get(JobRecord, "job-security") is not None
                    and self.session.get(SavedJobRecord, ("user-candidate", "job-security")) is None
                ):
                    self.session.add(SavedJobRecord(user_id="user-candidate", job_id="job-security"))
                self.session.flush()
        users = [User(row.id, row.email, row.role, row.password_hash, row.name, row.email_verified, row.auth_version) for row in self.session.scalars(select(UserRecord).order_by(UserRecord.position, UserRecord.id)).all()]
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
        activity_events = [
            ActivityEvent(row.id, row.event_type, row.occurred_at, row.actor_user_id,
                          row.actor_role, row.subject_type, row.subject_id, row.application_method,
                          row.origin)
            for row in self.session.scalars(
                select(ActivityEventRecord).order_by(ActivityEventRecord.occurred_at, ActivityEventRecord.id)
            ).all()
        ]
        from .store import InMemoryStore

        return InMemoryStore(users, companies, jobs, applications, profiles, saved_jobs,
                             memberships, notifications, activity_events)

    def replace(self, store):
        """Atomically mirror a domain-store snapshot, including removals."""
        models_in_delete_order = [
            ActivityEventRecord, NotificationRecord, SavedJobRecord, MembershipRecord, ProfileRecord,
            ApplicationRecord, JobRecord, CompanyRecord, UserRecord,
        ]
        for model in models_in_delete_order:
            self.session.execute(delete(model))
        self.session.flush()
        for position, item in enumerate(store.users):
            self.session.add(UserRecord(id=item.id, email=item.email, role=item.role, password_hash=item.password_hash, name=item.name, email_verified=item.email_verified, auth_version=item.auth_version, position=position))
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
        for item in store.activity_events:
            self.session.add(ActivityEventRecord(
                id=item.id, event_type=item.event_type, occurred_at=item.occurred_at,
                actor_user_id=item.actor_user_id, actor_role=item.actor_role,
                subject_type=item.subject_type, subject_id=item.subject_id,
                application_method=item.application_method, origin=item.origin,
            ))
        self.session.flush()

    def apply_changes(self, before, after):
        """Persist only records changed by this request.

        Requests take a SQLite ``BEGIN IMMEDIATE`` lock before hydration, so
        their before/after snapshots are serialized with other API requests.
        This diff also makes read-only requests issue no table writes.
        """
        def sync(model, old_items, new_items, key_of, record_of):
            old_by_key = {key_of(item): item for item in old_items}
            new_by_key = {key_of(item): item for item in new_items}
            for key in old_by_key.keys() - new_by_key.keys():
                record = self.session.get(model, key)
                if record is not None:
                    self.session.delete(record)
            for key, item in new_by_key.items():
                if key not in old_by_key or item != old_by_key[key]:
                    self.session.merge(record_of(item, key))

        sync(
            UserRecord, before.users, after.users, lambda item: item.id,
            lambda item, key: UserRecord(id=key, email=item.email, role=item.role, password_hash=item.password_hash,
                                          name=item.name, email_verified=item.email_verified, auth_version=item.auth_version,
                                          position=after.users.index(item)),
        )
        sync(
            CompanyRecord, before.companies, after.companies, lambda item: item.id,
            lambda item, key: CompanyRecord(id=key, name=item.name, description=item.description, website=item.website,
                                             logo=item.logo, accent=item.accent, position=after.companies.index(item)),
        )
        sync(
            JobRecord, before.jobs, after.jobs, lambda item: item.id,
            lambda item, key: JobRecord(
                id=key, company_id=item.company_id, title=item.title, description=item.description, location=item.location,
                salary_min=item.salary_min, salary_max=item.salary_max, currency=item.currency, remote_policy=item.remote_policy,
                job_type=item.job_type, experience_level=item.experience_level, skills=item.skills or [],
                responsibilities=item.responsibilities or [], qualifications=item.qualifications or [], benefits=item.benefits or [],
                application_method=item.application_method, external_apply_url=item.external_apply_url, status=item.status,
                posted_at=item.posted_at, deadline=item.deadline, application_count=item.application_count,
                position=after.jobs.index(item),
            ),
        )
        sync(
            ApplicationRecord, before.applications, after.applications, lambda item: item.id,
            lambda item, key: ApplicationRecord(
                id=key, job_id=item.job_id, candidate_id=item.candidate_id, status=item.status,
                candidate_name=item.candidate_name, candidate_email=item.candidate_email, cv_name=item.cv_name,
                cover_letter=item.cover_letter, created_at=item.created_at, position=after.applications.index(item),
            ),
        )
        sync(
            ProfileRecord, list(before.profiles.items()), list(after.profiles.items()), lambda pair: pair[0],
            lambda pair, key: ProfileRecord(user_id=key, data=dict(pair[1])),
        )
        sync(
            SavedJobRecord,
            [(user_id, job_id) for user_id, job_ids in before.saved_jobs.items() for job_id in job_ids],
            [(user_id, job_id) for user_id, job_ids in after.saved_jobs.items() for job_id in job_ids],
            lambda pair: pair, lambda pair, key: SavedJobRecord(user_id=key[0], job_id=key[1]),
        )
        sync(
            MembershipRecord, before.memberships, after.memberships,
            lambda item: (item.user_id, item.company_id),
            lambda item, key: MembershipRecord(user_id=key[0], company_id=key[1], role=item.role,
                                               position=after.memberships.index(item)),
        )
        sync(
            NotificationRecord, before.notifications, after.notifications, lambda item: item.id,
            lambda item, key: NotificationRecord(
                id=key, user_id=item.user_id, title=item.title, body=item.body, read_at=item.read_at,
                created_at=item.created_at, position=after.notifications.index(item),
            ),
        )
        sync(
            ActivityEventRecord, before.activity_events, after.activity_events, lambda item: item.id,
            lambda item, key: ActivityEventRecord(
                id=key, event_type=item.event_type, occurred_at=item.occurred_at,
                actor_user_id=item.actor_user_id, actor_role=item.actor_role,
                subject_type=item.subject_type, subject_id=item.subject_id,
                application_method=item.application_method, origin=item.origin,
            ),
        )
        self.session.flush()
