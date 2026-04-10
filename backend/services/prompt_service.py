from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config.settings import get_settings
from backend.db.models import PromptVersion
from backend.domain.enums import AnalysisModuleKey
from backend.schemas.persona_analysis import PromptVersionSchema


INITIAL_PROMPT_VERSION_NOTE = "初始结构化 Prompt"


def _to_schema(prompt_version: PromptVersion) -> PromptVersionSchema:
    return PromptVersionSchema(
        prompt_version_id=prompt_version.id,
        tool_key=prompt_version.tool_key,
        task_key=prompt_version.task_key,
        version_label=prompt_version.version_label,
        version_note=prompt_version.version_note,
        content=prompt_version.content,
        is_active=prompt_version.is_active,
        created_at=prompt_version.created_at,
        updated_at=prompt_version.updated_at,
    )


def ensure_default_prompt_versions(db: Session) -> list[PromptVersion]:
    settings = get_settings()
    prompts: list[PromptVersion] = []
    for prompt_config in settings.persona_analysis.get_prompt_configs():
        prompt_path = settings.resolve_path(prompt_config.default_prompt_path)
        prompt_text = prompt_path.read_text(encoding="utf-8") if Path(prompt_path).exists() else ""
        existing_prompt = db.scalar(
            select(PromptVersion)
            .where(PromptVersion.tool_key == prompt_config.tool_key)
            .where(PromptVersion.task_key == prompt_config.task_key)
            .order_by(PromptVersion.created_at.asc())
        )
        if existing_prompt:
            existing_prompt = _sync_untouched_default_prompt(
                db,
                prompt_config=prompt_config,
                prompt_text=prompt_text,
                existing_prompt=existing_prompt,
            )
            if not existing_prompt.is_active:
                existing_prompt.is_active = True
                db.add(existing_prompt)
                db.commit()
                db.refresh(existing_prompt)
            prompts.append(existing_prompt)
            continue

        prompt_version = PromptVersion(
            tool_key=prompt_config.tool_key,
            task_key=prompt_config.task_key,
            version_label=prompt_config.default_version_label,
            version_note=INITIAL_PROMPT_VERSION_NOTE,
            content=prompt_text,
            is_active=True,
        )
        db.add(prompt_version)
        db.commit()
        db.refresh(prompt_version)
        prompts.append(prompt_version)

    return prompts


def _sync_untouched_default_prompt(
    db: Session,
    *,
    prompt_config,
    prompt_text: str,
    existing_prompt: PromptVersion,
) -> PromptVersion:
    prompt_versions = list(
        db.scalars(
            select(PromptVersion)
            .where(PromptVersion.tool_key == prompt_config.tool_key)
            .where(PromptVersion.task_key == prompt_config.task_key)
            .order_by(PromptVersion.created_at.asc())
        )
    )

    if len(prompt_versions) != 1:
        return existing_prompt
    if existing_prompt.version_label != prompt_config.default_version_label:
        return existing_prompt
    if existing_prompt.based_on_prompt_version_id is not None:
        return existing_prompt
    if (existing_prompt.version_note or "").strip() != INITIAL_PROMPT_VERSION_NOTE:
        return existing_prompt

    if existing_prompt.content.strip() == prompt_text.strip():
        return existing_prompt

    existing_prompt.content = prompt_text
    db.add(existing_prompt)
    db.commit()
    db.refresh(existing_prompt)
    return existing_prompt


def ensure_default_prompt_version(db: Session) -> PromptVersion:
    prompts = ensure_default_prompt_versions(db)
    return prompts[0]


def list_prompt_versions(db: Session, tool_key: str, task_key: str) -> tuple[list[PromptVersionSchema], str | None]:
    prompt_versions = list(
        db.scalars(
            select(PromptVersion)
            .where(PromptVersion.tool_key == tool_key)
            .where(PromptVersion.task_key == task_key)
            .order_by(PromptVersion.created_at.desc())
        )
    )
    active_prompt = next(
        (item for item in prompt_versions if item.is_active), None)
    return [_to_schema(item) for item in prompt_versions], active_prompt.id if active_prompt else None


def get_prompt_version_by_id(db: Session, prompt_version_id: str) -> PromptVersion | None:
    return db.get(PromptVersion, prompt_version_id)


def get_active_prompt_version(
    db: Session,
    module_key: AnalysisModuleKey = AnalysisModuleKey.USER_PROFILE_AND_REPLY,
) -> PromptVersion:
    settings = get_settings()
    prompt_config = settings.persona_analysis.get_prompt_config(module_key)
    prompt_version = db.scalar(
        select(PromptVersion)
        .where(PromptVersion.tool_key == prompt_config.tool_key)
        .where(PromptVersion.task_key == prompt_config.task_key)
        .where(PromptVersion.is_active.is_(True))
        .order_by(PromptVersion.updated_at.desc())
    )
    if prompt_version:
        return prompt_version
    return ensure_default_prompt_version(db)


def create_prompt_version(
    db: Session,
    *,
    tool_key: str,
    task_key: str,
    version_label: str,
    version_note: str | None,
    content: str,
    based_on_prompt_version_id: str | None,
    is_active: bool,
) -> PromptVersion:
    prompt_version = PromptVersion(
        tool_key=tool_key,
        task_key=task_key,
        version_label=version_label,
        version_note=version_note,
        content=content,
        based_on_prompt_version_id=based_on_prompt_version_id,
        is_active=is_active,
    )
    if is_active:
        _deactivate_other_versions(db, tool_key, task_key)

    db.add(prompt_version)
    db.commit()
    db.refresh(prompt_version)
    return prompt_version


def update_prompt_version(
    db: Session,
    prompt_version: PromptVersion,
    *,
    version_note: str | None,
    content: str | None,
) -> PromptVersion:
    if version_note is not None:
        prompt_version.version_note = version_note
    if content is not None:
        prompt_version.content = content
    db.add(prompt_version)
    db.commit()
    db.refresh(prompt_version)
    return prompt_version


def activate_prompt_version(db: Session, prompt_version: PromptVersion) -> PromptVersion:
    _deactivate_other_versions(
        db, prompt_version.tool_key, prompt_version.task_key)
    prompt_version.is_active = True
    db.add(prompt_version)
    db.commit()
    db.refresh(prompt_version)
    return prompt_version


def _deactivate_other_versions(db: Session, tool_key: str, task_key: str) -> None:
    prompt_versions = list(
        db.scalars(
            select(PromptVersion)
            .where(PromptVersion.tool_key == tool_key)
            .where(PromptVersion.task_key == task_key)
            .where(PromptVersion.is_active.is_(True))
        )
    )
    for item in prompt_versions:
        item.is_active = False
        db.add(item)


def load_system_template(module_key: AnalysisModuleKey) -> str:
    """Load the backend system template for a given analysis module.

    The system template contains I/O format specs, output scope constraints and
    self-check requirements. It is NOT user-editable; users only edit the core
    analysis logic stored in PromptVersion.content.
    """
    settings = get_settings()
    template_path = settings.resolve_path(
        settings.persona_analysis.get_system_template_path(module_key)
    )
    if not Path(template_path).exists():
        return ""
    return template_path.read_text(encoding="utf-8")


def assemble_full_prompt(module_key: AnalysisModuleKey, user_content: str) -> str:
    """Combine user-editable core logic with the backend system template.

    The assembled prompt is what gets sent to the LLM. Format:
        {user_content}

        ---

        {system_template}
    """
    system_template = load_system_template(module_key)
    if not system_template:
        return user_content
    return f"{user_content}\n\n---\n\n{system_template}"
