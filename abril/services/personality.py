"""Plantillas de personalidad como capa opcional sobre la identidad inmutable.

Nunca modifica `SYSTEM_PROMPT`, `CREATOR_COMPANY`, `ASSISTANT_NAME` ni `BANNER`.
Solo añade prefijos de estilo/tema que el usuario puede activar/desactivar
con el flag `personality_templates`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PersonalityTemplate(Enum):
    DEFAULT = "default"          # Sin capa extra (identidad pura)
    TECNICA = "tecnica"          # Respuestas técnicas, concisas, con ejemplos de código
    CREATIVA = "creativa"        # Tonos más narrativos, metáforas, brainstorming
    DOCENTE = "docente"          # Explicaciones paso a paso, didácticas
    CONCISE = "concisa"          # Respuestas ultra-cortas, solo lo esencial
    EMPATICA = "empatica"        # Tonos cálidos, validación emocional


@dataclass
class TemplateConfig:
    name: PersonalityTemplate
    description: str
    system_prefix: str
    # Parámetros de generación sugeridos
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.1


_TEMPLATES: dict[PersonalityTemplate, TemplateConfig] = {
    PersonalityTemplate.DEFAULT: TemplateConfig(
        name=PersonalityTemplate.DEFAULT,
        description="Identidad pura de Abril (Nexora), sin capa extra.",
        system_prefix="",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
    ),
    PersonalityTemplate.TECNICA: TemplateConfig(
        name=PersonalityTemplate.TECNICA,
        description="Modo técnico: respuestas concisas, código, comandos, sin florituras.",
        system_prefix=(
            "\n[MODO TÉCNICO] Responde de forma concisa y precisa. "
            "Prioriza ejemplos de código, comandos y salida estructurada. "
            "Evita explicaciones innecesarias."
        ),
        temperature=0.3,
        top_p=0.95,
        repeat_penalty=1.05,
    ),
    PersonalityTemplate.CREATIVA: TemplateConfig(
        name=PersonalityTemplate.CREATIVA,
        description="Modo creativo: narrativo, brainstorming, metáforas.",
        system_prefix=(
            "\n[MODO CREATIVO] Usa un tono narrativo y exploratorio. "
            "Fomenta ideas laterales, metáforas y conexiones inesperadas. "
            "No te limites a lo literal."
        ),
        temperature=0.9,
        top_p=0.95,
        repeat_penalty=1.15,
    ),
    PersonalityTemplate.DOCENTE: TemplateConfig(
        name=PersonalityTemplate.DOCENTE,
        description="Modo docente: explicaciones paso a paso, ejemplos progresivos.",
        system_prefix=(
            "\n[MODO DOCENTE] Explica conceptos desglosados en pasos claros. "
            "Usa analogías, ejemplos progresivos y verifica comprensión. "
            "Adapta el nivel técnico al usuario."
        ),
        temperature=0.6,
        top_p=0.9,
        repeat_penalty=1.1,
    ),
    PersonalityTemplate.CONCISE: TemplateConfig(
        name=PersonalityTemplate.CONCISE,
        description="Modo conciso: respuestas mínimas, solo lo esencial.",
        system_prefix=(
            "\n[MODO CONCISO] Responde en la menor cantidad de palabras posible. "
            "Solo la respuesta directa, sin introducción ni cierre. "
            "Omite contexto salvo que se pida explícitamente."
        ),
        temperature=0.2,
        top_p=0.9,
        repeat_penalty=1.05,
    ),
    PersonalityTemplate.EMPATICA: TemplateConfig(
        name=PersonalityTemplate.EMPATICA,
        description="Modo empático: validación emocional, tono cálido.",
        system_prefix=(
            "\n[MODO EMPÁTICO] Reconoce y valida el estado emocional del usuario. "
            "Usa un tono cálido y de apoyo. Prioriza la escucha activa "
            "antes de dar soluciones técnicas."
        ),
        temperature=0.8,
        top_p=0.9,
        repeat_penalty=1.1,
    ),
}


def get_template(template: PersonalityTemplate) -> TemplateConfig:
    return _TEMPLATES.get(template, _TEMPLATES[PersonalityTemplate.DEFAULT])


def list_templates() -> list[TemplateConfig]:
    return list(_TEMPLATES.values())


def build_system_prompt(base_prompt: str, template: PersonalityTemplate) -> str:
    """
    Construye el system prompt final combinando la identidad inmutable
    con el prefijo de la plantilla (si no es DEFAULT).
    """
    cfg = get_template(template)
    if template == PersonalityTemplate.DEFAULT:
        return base_prompt
    return base_prompt + cfg.system_prefix


def suggest_template(text: str) -> PersonalityTemplate:
    """Heurística simple para sugerir plantilla según la entrada."""
    low = text.lower()
    if any(k in low for k in ("código", "code", "script", "debug", "error", "terminal", "comando")):
        return PersonalityTemplate.TECNICA
    if any(k in low for k in ("idea", "crea", "inventa", "brainstorm", "historia", "poema")):
        return PersonalityTemplate.CREATIVA
    if any(k in low for k in ("explica", "cómo", "por qué", "enseña", "enséñame", "aprende", "tutorial")):
        return PersonalityTemplate.DOCENTE
    if any(k in low for k in ("resume", "corto", "breve", "tl;dr", "resumen")):
        return PersonalityTemplate.CONCISE
    if any(k in low for k in ("triste", "ansioso", "preocupado", "ayuda", "apoyo", "siento")):
        return PersonalityTemplate.EMPATICA
    return PersonalityTemplate.DEFAULT


__all__ = [
    "PersonalityTemplate",
    "TemplateConfig",
    "get_template",
    "list_templates",
    "build_system_prompt",
    "suggest_template",
]