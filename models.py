import uuid
from enum import Enum

from sqlalchemy import (CHAR, JSON, Boolean, Column, DateTime, ForeignKey,
                        Text, UniqueConstraint)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import (DeclarativeBase, backref, mapped_column,
                            relationship)
from sqlalchemy.types import Integer, String
from sqlalchemy_utils import (ChoiceType, JSONType, StringEncryptedType,
                              Timestamp)
from sqlalchemy_utils.types import UUIDType


def _secret_key():
    return "CHANGE_ME"


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


json_field = (
    JSON()
    .with_variant(
        postgresql.JSONB(none_as_null=True),
        "postgresql",
    )
    .with_variant(
        JSONType(),
        "sqlite",
    )
    .with_variant(
        JSONType(),
        "mysql",
    )
)


class User(Base, Timestamp):
    """User data model."""

    __tablename__ = "accounts_user"

    id = mapped_column(Integer, primary_key=True)

    username = Column("username", String(255), nullable=True, unique=True)

    """Lower-case version of the username, to assert uniqueness."""

    displayname = Column("displayname", String(255), nullable=True)
    """Case-preserving version of the username."""

    email = Column("email", String(255), unique=True)
    """User email."""

    domain = Column(String(255), nullable=True)
    """Domain of email."""

    password = Column(String(255))
    """User password."""

    active = Column(Boolean(name="active"))
    """Flag to say if the user is active or not ."""

    confirmed_at = Column(DateTime)
    """When the user confirmed the email address."""

    # Enables SQLAlchemy version counter
    version_id = Column(Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    user_profile = Column(
        "profile",
        json_field,
        default=lambda: dict(),
        nullable=True,
    )
    """The user profile as a JSON field."""

    preferences = Column(
        "preferences",
        json_field,
        default=lambda: dict(),
        nullable=True,
    )
    """The user's preferences stored in a JSON field."""

    __mapper_args__ = {"version_id_col": version_id}

    blocked_at = Column(
        DateTime,
        nullable=True,
    )

    verified_at = Column(
        DateTime,
        nullable=True,
    )


class Repository(Base, Timestamp):
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

    repository = relationship(Repository, backref=backref("releases", lazy="dynamic"))

    # event = db.relationship(Event)

    def __repr__(self):
        """Get release representation."""
        return f"<Release {self.tag}:{self.release_id} ({self.status.title})>"


class RemoteAccount(Base, Timestamp):
    """Storage for remote linked accounts."""

    __tablename__ = "oauthclient_remoteaccount"

    __table_args__ = (UniqueConstraint("user_id", "client_id"),)

    #
    # Fields
    #
    id = Column(Integer, primary_key=True, autoincrement=True)
    """Primary key."""

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    """Local user linked with a remote app via the access token."""

    client_id = Column(String(255), nullable=False)
    """Client ID of remote application (defined in OAUTHCLIENT_REMOTE_APPS)."""

    extra_data = Column(MutableDict.as_mutable(JSONType), nullable=False)
    """Extra data associated with this linked account."""

    #
    # Relationships properties
    #
    user = relationship(User, backref="remote_accounts")
    """SQLAlchemy relationship to user."""


class RemoteToken(Base, Timestamp):
    """Storage for the access tokens for linked accounts."""

    __tablename__ = "oauthclient_remotetoken"

    #
    # Fields
    #
    id_remote_account = Column(
        Integer,
        ForeignKey(RemoteAccount.id, name="fk_oauthclient_remote_token_remote_account"),
        nullable=False,
        primary_key=True,
    )
    """Foreign key to account."""

    token_type = Column(String(40), default="", nullable=False, primary_key=True)
    """Type of token."""

    access_token = Column(
        StringEncryptedType(type_in=Text, key=_secret_key), nullable=False
    )
    """Access token to remote application."""

    secret = Column(Text(), default="", nullable=False)
    """Used only by OAuth 1."""

    #
    # Relationships properties
    #
    remote_account = relationship(
        RemoteAccount, backref=backref("remote_tokens", cascade="all, delete-orphan")
    )
