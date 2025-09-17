import uuid
from enum import Enum

from sqlalchemy import CHAR, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, backref, mapped_column, relationship
from sqlalchemy.types import Integer, String
from sqlalchemy_utils import ChoiceType, JSONType, Timestamp
from sqlalchemy_utils.types import UUIDType


class Base(DeclarativeBase):
    pass


RELEASE_STATUS_TITLES = {
    "RECEIVED": "Received",
    "PROCESSING": "Processing",
    "PUBLISHED": "Published",
    "FAILED": "Failed",
    "DELETED": "Deleted",
}

RELEASE_STATUS_ICON = {
    "RECEIVED": "spinner loading icon",
    "PROCESSING": "spinner loading icon",
    "PUBLISHED": "check icon",
    "FAILED": "times icon",
    "DELETED": "times icon",
}

RELEASE_STATUS_COLOR = {
    "RECEIVED": "warning",
    "PROCESSING": "warning",
    "PUBLISHED": "positive",
    "FAILED": "negative",
    "DELETED": "negative",
}


class ReleaseStatus(Enum):
    """Constants for possible status of a Release."""

    __order__ = "RECEIVED PROCESSING PUBLISHED FAILED DELETED"

    RECEIVED = "R"
    """Release has been received and is pending processing."""

    PROCESSING = "P"
    """Release is still being processed."""

    PUBLISHED = "D"
    """Release was successfully processed and published."""

    FAILED = "F"
    """Release processing has failed."""

    DELETED = "E"
    """Release has been deleted."""

    def __init__(self, value):
        """Hack."""

    def __eq__(self, other):
        """Equality test."""
        return self.value == other

    def __str__(self):
        """Return its value."""
        return self.value

    @property
    def title(self):
        """Return human readable title."""
        return RELEASE_STATUS_TITLES[self.name]

    @property
    def icon(self):
        """Font Awesome status icon."""
        return RELEASE_STATUS_ICON[self.name]

    @property
    def color(self):
        """UI status color."""
        return RELEASE_STATUS_COLOR[self.name]


class User(DeclarativeBase):
    """User data model."""

    __tablename__ = "accounts_user"

    id = mapped_column(Integer, primary_key=True)


class Repository(Base):
    __tablename__ = "github_repositories"
    id = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Repository identifier."""

    github_id = mapped_column(
        Integer,
        unique=True,
        index=True,
        nullable=True,
    )

    name = mapped_column(String(255), unique=True, index=True, nullable=False)
    """Fully qualified name of the repository including user/organization."""

    user_id = mapped_column(Integer, ForeignKey(User.id), nullable=True)
    """Reference user that can manage this repository."""

    hook = mapped_column(Integer)
    """Hook identifier."""

    #
    # Relationships
    #
    user = relationship(User)


class Release(Base, Timestamp):
    """Information about a GitHub release."""

    __tablename__ = "github_releases"

    id = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Release identifier."""

    release_id = mapped_column(Integer, unique=True, nullable=True)
    """Unique GitHub release identifier."""

    tag = mapped_column(String(255))
    """Release tag."""

    errors = mapped_column(
        JSONType().with_variant(
            # TODO postgresql specific. Limits the usage of the DB engine.
            postgresql.JSON(none_as_null=True),
            "postgresql",
        ),
        nullable=True,
    )
    """Release processing errors."""

    repository_id = mapped_column(UUIDType, ForeignKey(Repository.id))
    """Repository identifier."""

    # event_id = mapped_column(UUIDType, db.ForeignKey(Event.id), nullable=True)
    """Incoming webhook event identifier."""

    record_id = mapped_column(
        UUIDType,
        index=True,
        nullable=True,
    )
    """Weak reference to a record identifier."""

    status = mapped_column(
        ChoiceType(ReleaseStatus, impl=CHAR(1)),
        nullable=False,
    )
    """Status of the release, e.g. 'processing', 'published', 'failed', etc."""

    repository = relationship(
        Repository, backref=backref("releases", lazy="dynamic")
    )

    # event = db.relationship(Event)

    def __repr__(self):
        """Get release representation."""
        return f"<Release {self.tag}:{self.release_id} ({self.status.title})>"
