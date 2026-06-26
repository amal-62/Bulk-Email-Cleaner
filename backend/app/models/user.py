# Import column types we'll use to define our table structure
from sqlalchemy import Column, String, DateTime, Text
# UUID is a PostgreSQL-specific column type for unique IDs
from sqlalchemy.dialects.postgresql import UUID
# Import Base so this model registers itself as a database table
from app.database import Base
import uuid                 # Python's built-in UUID generator
from datetime import datetime, timezone  # For timestamps

# This class represents the 'users' table in PostgreSQL
# Every attribute that's a Column becomes a column in the table
class User(Base):
    __tablename__ = "users"  # The actual table name in the database

    # Primary key — unique ID for each user
    # UUID is better than integers: harder to guess, works across distributed systems
    # default=uuid.uuid4 means Python auto-generates a UUID when creating a new user
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # The user's Gmail address — must be unique (no two users with same email)
    # nullable=False means this field is required
    email = Column(String, unique=True, nullable=False)

    # User's display name from their Google profile (optional)
    name = Column(String)

    # URL to their Google profile picture (optional, can be long so we use Text)
    picture = Column(Text)

    # Google access token — short-lived token used to call Gmail API
    # Stored as Text because tokens can be long strings
    access_token = Column(Text)

    # Google refresh token — long-lived token used to get new access tokens
    # This is the most sensitive piece of data we store
    refresh_token = Column(Text)

    # When the user first signed up — auto-set to current UTC time
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))