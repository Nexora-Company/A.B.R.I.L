"""Plantillas de personalidad tests."""

from __future__ import annotations

from abril.services.personality import (
    PersonalityTemplate,
    TemplateConfig,
    build_system_prompt,
    suggest_template,
    list_templates,
    get_template,
)


def test_default_template_is_identity_only():
    cfg = get_template(PersonalityTemplate.DEFAULT)
    assert cfg.name == PersonalityTemplate.DEFAULT
    assert cfg.system_prefix == ""


def test_technical_template_adds_prefix():
    base = "Eres Abril."
    result = build_system_prompt(base, PersonalityTemplate.TECNICA)
    assert "[MODO TÉCNICO]" in result
    assert result.startswith(base)


def test_all_templates_have_config():
    for template in PersonalityTemplate:
        cfg = get_template(template)
        assert isinstance(cfg, TemplateConfig)
        assert cfg.temperature >= 0
        assert cfg.top_p > 0


def test_list_templates_returns_all():
    templates = list_templates()
    assert len(templates) == len(PersonalityTemplate)


def test_suggest_template_technical():
    assert suggest_template("escribe un script en python") == PersonalityTemplate.TECNICA
    assert suggest_template("debug este error") == PersonalityTemplate.TECNICA


def test_suggest_template_creative():
    assert suggest_template("inventa una historia") == PersonalityTemplate.CREATIVA
    assert suggest_template("brainstorm ideas") == PersonalityTemplate.CREATIVA


def test_suggest_template_docente():
    assert suggest_template("explica cómo funciona") == PersonalityTemplate.DOCENTE
    assert suggest_template("enséñame python") == PersonalityTemplate.DOCENTE


def test_suggest_template_concise():
    assert suggest_template("resume en breve") == PersonalityTemplate.CONCISE
    assert suggest_template("tl;dr") == PersonalityTemplate.CONCISE


def test_suggest_template_empathetic():
    assert suggest_template("me siento triste") == PersonalityTemplate.EMPATICA
    assert suggest_template("necesito apoyo") == PersonalityTemplate.EMPATICA


def test_suggest_template_default_fallback():
    assert suggest_template("hola que tal") == PersonalityTemplate.DEFAULT