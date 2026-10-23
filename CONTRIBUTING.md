# Contribuir a A.B.R.I.L

Bienvenido. El código es visible y las contribuciones son bienvenidas.

## Antes de empezar

Abre un issue para discutir cambios grandes antes de implementarlos.

## Flujo de trabajo

1. Fork del repositorio.
2. Crea una rama: `feat/`, `fix/`, `docs/`.
3. Commits con Conventional Commits.
4. Abre un Pull Request.

## Entorno de desarrollo

Comandos reales del repositorio (no hay manifiesto de dependencias: solo stdlib de Python):

```sh
python3 -m py_compile main.py abril/**/*.py
python3 -m mypy main.py abril/        # opcional
ruff check main.py abril/             # opcional
ruff format --check main.py abril/    # opcional
```

## Estándares de código

- Python 3.10+.
- Formato: `ruff format` (88 columnas).
- Lint: `ruff check`.
- Tipado: type hints en funciones públicas; `mypy --strict` opcional.
- Imports absolutos desde `abril.`; orden stdlib → third-party → local.
- Docstrings estilo Google en módulos, clases y funciones públicas.
- Sin dependencias externas sin discusión previa.

## Checklist del Pull Request

- [ ] `main` actualizado y rebaseado/mergeado.
- [ ] Commits atómicos + Conventional Commits.
- [ ] `python3 -m py_compile main.py abril/**/*.py` pasa.
- [ ] `mypy` y `ruff` pasan (si se usan).
- [ ] Docstrings actualizadas.
- [ ] README actualizado si cambia configuración, uso o arquitectura.
- [ ] Sin `.env`, `__pycache__`, `*.pyc`, logs en el diff.
- [ ] PR explica qué y por qué.

## Proceso de revisión

El mantenedor revisa los PRs. Espera comentarios y solicitudes de cambio antes de la fusión.

## Acuerdo de contribución (CLA)

Al enviar una contribución, la persona declara que es autora o tiene derecho a aportarla y concede a Nexora una licencia perpetua, mundial, no exclusiva, gratuita e irrevocable para usar, modificar, sublicenciar, relicenciar y comercializar la contribución, incluso bajo otras licencias.

<!-- TODO: revisión legal del texto del CLA -->

## Código de conducta

Reglas breves de respeto y convivencia: trato respetuoso, sin acoso, sin ataques personales. Los conflictos se resuelven con diálogo.

## Licencia

Las contribuciones quedan bajo **PolyForm Noncommercial 1.0.0**, sujetas al acuerdo anterior.