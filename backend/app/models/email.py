from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  # must match User.id's type exactly
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)

    # UUID here (not Integer) because it has to match users.id's type
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    gmail_message_id = Column(String, unique=True, nullable=False, index=True)  # unique so re-syncing doesn't duplicate rows

    sender_email = Column(String, nullable=False, index=True)  # indexed — this is what we group/filter by constantly
    sender_name = Column(String, nullable=True)

    subject = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=True)

    has_unsubscribe_header = Column(Boolean, default=False)  # main spam/newsletter signal
    unsubscribe_url = Column(String, nullable=True)

    is_trashed = Column(Boolean, default=False)  # lets UI hide already-actioned emails
    synced_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="emails")  # fixed the mismatch from before