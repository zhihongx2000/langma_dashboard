from __future__ import annotations

from fastapi import HTTPException, status

from backend.config.settings import ModelOptionConfig, get_settings
from backend.schemas.persona_analysis import ModelOptionSchema


def list_model_options() -> list[ModelOptionSchema]:
    settings = get_settings()
    return [
        ModelOptionSchema(
            provider_key=item.provider_key,
            provider_label=item.provider_label,
            model_key=item.model_key,
            model_label=item.model_label,
            is_default=item.is_default,
            is_enabled=item.is_enabled,
            temperature=item.temperature,
            max_tokens=item.max_tokens,
        )
        for item in settings.persona_analysis.model_options
        if item.is_enabled
    ]


def get_model_option(model_key: str) -> ModelOptionSchema:
    model_config = get_model_config(model_key)
    return ModelOptionSchema(
        provider_key=model_config.provider_key,
        provider_label=model_config.provider_label,
        model_key=model_config.model_key,
        model_label=model_config.model_label,
        is_default=model_config.is_default,
        is_enabled=model_config.is_enabled,
        temperature=model_config.temperature,
        max_tokens=model_config.max_tokens,
    )


def get_model_config(model_key: str) -> ModelOptionConfig:
    settings = get_settings()
    for item in settings.persona_analysis.model_options:
        if item.is_enabled and item.model_key == model_key:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"未找到模型配置：{model_key}",
    )


def get_default_model_option() -> ModelOptionSchema:
    model_options = list_model_options()
    for model_option in model_options:
        if model_option.is_default:
            return model_option
    if not model_options:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="未配置可用模型")
    return model_options[0]
