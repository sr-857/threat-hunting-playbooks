"""Database model for scheduled hunts."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class HuntSchedule(Base):
    __tablename__ = "hunt_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    playbook_id = Column(String(36), ForeignKey("playbooks.id"), nullable=False)
    cron_expression = Column(String(64), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    playbook = relationship("Playbook", backref="schedules")

    def __repr__(self) -> str:
        return f"HuntSchedule(id={self.id!r}, name={self.name!r}, playbook_id={self.playbook_id!r})"
