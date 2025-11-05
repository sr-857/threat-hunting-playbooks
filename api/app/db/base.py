"""Database model registration."""

from app.db.session import Base

from app.models import playbook  # noqa: F401  # Register models with metadata
from app.models import schedule  # noqa: F401

__all__ = ["Base"]
