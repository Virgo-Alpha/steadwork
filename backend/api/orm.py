"""SQLAlchemy mappings for the domain records held by the API store."""

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    profile: Mapped["ProfileRecord | None"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    saved_jobs: Mapped[list["SavedJobRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memberships: Mapped[list["MembershipRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["NotificationRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class CompanyRecord(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    website: Mapped[str] = mapped_column(String, nullable=False, default="")
    logo: Mapped[str] = mapped_column(String, nullable=False, default="")
    accent: Mapped[str] = mapped_column(String, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs: Mapped[list["JobRecord"]] = relationship(back_populates="company")
    memberships: Mapped[list["MembershipRecord"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class JobRecord(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    location: Mapped[str] = mapped_column(String, nullable=False, default="")
    salary_min: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    salary_max: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")
    remote_policy: Mapped[str] = mapped_column(String, nullable=False, default="On-site")
    job_type: Mapped[str] = mapped_column(String, nullable=False, default="Full-time")
    experience_level: Mapped[str] = mapped_column(String, nullable=False, default="Mid")
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    responsibilities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    qualifications: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    benefits: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    application_method: Mapped[str] = mapped_column(String, nullable=False, default="Internal")
    external_apply_url: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Draft")
    posted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    application_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    company: Mapped[CompanyRecord] = relationship(back_populates="jobs")
    applications: Mapped[list["ApplicationRecord"]] = relationship(back_populates="job")
    saved_by: Mapped[list["SavedJobRecord"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class ApplicationRecord(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False, index=True)
    candidate_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    candidate_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    candidate_email: Mapped[str] = mapped_column(String, nullable=False, default="")
    cv_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    job: Mapped[JobRecord] = relationship(back_populates="applications")


class ProfileRecord(Base):
    __tablename__ = "candidate_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    user: Mapped[UserRecord] = relationship(back_populates="profile")


class SavedJobRecord(Base):
    __tablename__ = "saved_jobs"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    user: Mapped[UserRecord] = relationship(back_populates="saved_jobs")
    job: Mapped[JobRecord] = relationship(back_populates="saved_by")


class MembershipRecord(Base):
    __tablename__ = "company_memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    user: Mapped[UserRecord] = relationship(back_populates="memberships")
    company: Mapped[CompanyRecord] = relationship(back_populates="memberships")


class NotificationRecord(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    user: Mapped[UserRecord] = relationship(back_populates="notifications")
