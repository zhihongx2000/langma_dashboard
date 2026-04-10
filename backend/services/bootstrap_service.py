from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.session import get_engine
from backend.services.prompt_service import ensure_default_prompt_versions


def initialize_database() -> None:
    Base.metadata.create_all(bind=get_engine())
    _apply_schema_migrations()


def _apply_schema_migrations() -> None:
    """Apply incremental schema changes that create_all cannot handle for existing tables."""
    engine = get_engine()
    with engine.connect() as conn:
        # Add module_key column to analysis_runs if it does not exist yet
        existing = conn.execute(
            text("PRAGMA table_info(analysis_runs)")
        ).fetchall()
        column_names = {row[1] for row in existing}
        if "module_key" not in column_names:
            conn.execute(
                text("ALTER TABLE analysis_runs ADD COLUMN module_key TEXT")
            )
            conn.commit()


def seed_defaults(db: Session) -> None:
    ensure_default_prompt_versions(db)
