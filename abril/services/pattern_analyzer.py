# ═════════════════════════════════════════════════════════════════════════════
#  ANALIZADOR DE PATRONES Y SUGERIDOR DE IDEAS (Fase C)
# ═════════════════════════════════════════════════════════════════════════════

MAX_PATTERN_CHARS = 30_000


class PatternAnalyzer:
    """Analiza patrones de uso, sugiere ideas y permite pensar profundamente."""

    def __init__(self, ui: TerminalUI, chat: ChatService, memory: MemoryService, actions: ActionsService) -> None:
        self.ui = ui
        self.chat = chat
        self.memory = memory
        self.actions = actions

    # ---------------------------------------------------------------- #
    #  Comandos de análisis y sugerencia
    # ---------------------------------------------------------------- #
    def handle(self, user_input: str) -> bool:
        """Devuelve True si el comando de patrón/idea fue manejado."""
        text = user_input.strip()
        if not text:
            return False

        parts = shlex.split(text)
        if not parts:
            return False
        cmd = parts[0].lower()

        if cmd == "/analizar":
            return self._cmd_analizar(parts[1:])
        if cmd == "/ideas":
            return self._cmd_ideas(parts[1:])
        if cmd == "/pensar":
            return self._cmd_pensar(parts[1:])
        return False

    # ── analizar ──
    def _cmd_analizar(self, args: list[str]) -> bool:
        """Analiza patrones en el historial de acciones, memoria o un archivo."""
        if not args:
            return self._analizar_contexto_general()
        target = args[0].lower()
        if target in {"acciones", "action", "historial", "history"}:
            return self._analizar_acciones()
        if target in {"memoria", "memory", "preferencias", "prefs"}:
            return self._analizar_memoria()
        if target in {"rutinas", "routines"}:
            return self._analizar_rutinas()
        path_str = args[0]
        return self._analizar_archivo(path_str)

    def _analizar_contexto_general(self) -> bool:
        audit = self.actions.audit_log()
        prefs = self.memory.get_preferences()
        routines = self.memory.list_routines()

        self.ui.print_system("Analizando tu contexto general...")

        partes = []
        if audit:
            partes.append("=== HISTORIAL DE ACCIONES ===")
            for entry in audit[-20:]:
                partes.append(f"{entry['time']} · {entry['action']} · {entry['detail']} — {entry['result']}")
        if prefs:
            partes.append("\\n=== PREFERENCIAS GUARDADAS ===")
            for k, v in prefs.items():
                partes.append(f"{k} = {v}")
        if routines:
            partes.append("\\n=== RUTINAS ===")
            for r in routines:
                estado = "confirmada" if r.get("confirmed") else "pendiente"
                partes.append(f"{r['name']} — {r.get('description', '')} [{estado}]")

        if not partes:
            self.ui.print_warning("No hay suficiente datos para analizar. Usa Abril un poco más.")
            return True

        contexto = "\\n".join(partes[:MAX_PATTERN_CHARS])

        system_prompt = (
            "Eres un analista de patrones experto. Analiza el siguiente contexto de uso del usuario "
            "y identifica: 1) patrones repetitivos, 2) hábitos que podrían automatizarse, "
            "3) oportunidades de mejora en su flujo de trabajo, 4) inconsistencias o cosas que "
            "no tienen sentido. Responde en español, de forma clara, práctica y amigable. "
            "Presenta los hallazgos como observaciones, no como órdenes."
        )

        self.ui.start_typing()
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Contexto de uso del usuario:\\n{contexto}"},
            ]
            answer = self.chat.provider.complete(messages)
            self.ui.stop_typing()
        except Exception as e:
            self.ui.stop_typing()
            self.ui.print_error(f"Error del modelo: {e}")
            return True

        self.ui.print_assistant(answer)
        return True

    def _analizar_acciones(self) -> bool:
        audit = self.actions.audit_log()
        if not audit:
            self.ui.print_warning("No hay historial de acciones para analizar.")
            return True

        partes = []
        for entry in audit[-30:]:
            partes.append(f"{entry['time']} · {entry['action']} · {entry['detail']} — {entry['result']}")
        contexto = "\\n".join(partes[:MAX_PATTERN_CHARS])

        system_prompt = (
            "Eres un analista de patrones. Analiza el historial de acciones del usuario e identifica: "
            "1) acciones que se repiten con frecuencia, 2) patrones de uso (horarios, tipos de archivos, apps), "
            "3) oportunidades de automatización que le ahorrarían tiempo. "
            "Responde en español, claro y práctico. Presenta hallazgos como observaciones."
        )

        self.ui.start_typing()
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Historial de acciones:\\n{contexto}"},
            ]
            answer = self.chat.provider.complete(messages)
            self.ui.stop_typing()
        except Exception as e:
            self.ui.stop_typing()
            self.ui.print_error(f"Error del modelo: {e}")
            return True

        self.ui.print_assistant(answer)
        return True

    def _analizar_memoria(self) -> bool:
        prefs = self.memory.get_preferences()
        if not prefs:
            self.ui.print_warning("No hay preferencias guardadas para analizar.")
            return True

        partes = []
        for k, v in prefs.items():
            partes.append(f"{k} = {v}")
        contexto = "\\n".join(partes[:MAX_PATTERN_CHARS])

        system_prompt = (
            "Eres un analista de preferencias. Analiza las preferencias guardadas del usuario e identifica: "
            "1) temas o herramientas que le interesan, 2) patrones en sus elecciones, "
            "3) sugerencias de nuevas preferencias que podría guardar basándote en lo que ya tiene. "
            "Responde en español, claro y práctico."
        )

        self.ui.start_typing()
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Preferencias del usuario:\\n{contexto}"},
            ]
            answer = self.chat.provider.complete(messages)
            self.ui.stop_typing()
        except Exception as e:
            self.ui.stop_typing()
            self.ui.print_error(f"Error del modelo: {e}")
            return True

        self.ui.print_assistant(answer)
        return True

    def _analizar_rutinas(self) -> bool:
        routines = self.memory.list_routines()
        if not routines:
            self.ui.print_warning("No hay rutinas guardadas para analizar.")
            return True

        partes = []
        for r in routines:
            estado = "confirmada" if r.get("confirmed") else "pendiente"
            partes.append(f"{r['name']} — {r.get('description', '')} [{estado}]")
        contexto = "\\n".join(partes[:MAX_PATTERN_CHARS])

        system_prompt = (
            "Eres un analista de rutinas. Analiza las rutinas guardadas del usuario e identifica: "
            "1) qué tipo de tareas automatiza, 2) oportunidades para crear nuevas rutinas, "
            "3) rutinas que podrían combinarse o simplificarse. "
            "Responde en español, claro y práctico."
        )

        self.ui.start_typing()
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Rutinas del usuario:\\n{contexto}"},
            ]
            answer = self.chat.provider.complete(messages)
            self.ui.stop_typing()
        except Exception as e:
            self.ui.stop_typing()
            self.ui.print_error(f"Error del modelo: {e}")
            return True

        self.ui.print_assistant(answer)
        return True

    def _analizar_archivo(self, path_str: str) -> bool:
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            self.ui.print_error(f"El archivo no existe: {path}")
            return True
        if not path.is_file():
            self.ui.print_error(f"No es un archivo: {path}")
            return True

        lang = detect_language(str(path))
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            self.ui.print_error(f"No se pudo leer el archivo: {e}")
            return True

        if len(content) > MAX_PATTERN_CHARS:
            content = content[:MAX_PATTERN_CHARS] + "\\n... [truncado] ..."

        self.ui.print_system(f"Analizando patrones en {path.name} ({lang})...")

        system_prompt = (
            f"Eres un analista de patrones experto en {lang}. Analiza el siguiente contenido e identifica: "
            "1) patrones repetitivos, 2) estructuras que aparecen varias veces, "
            "3) oportunidades de refactorización o automatización, "
            "4) inconsistencias o cosas que podrían mejorarse. "
            "Responde en español, claro y práctico."
        )

        self.ui.start_typing()
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Archivo: {path.name}\\nLenguaje: {lang}\\nContenido:\\n```{lang}\\n{content}\\n```"},
            ]
            answer = self.chat.provider.complete(messages)
            self.ui.stop_typing()
        except Exception as e:
            self.ui.stop_typing()
            self.ui.print_error(f"Error del modelo: {e}")
            return True

        self.ui.print_assistant(answer)
        return True

    # ── ideas ──
    def _cmd_ideas(self, args: list[str]) -> bool:
        prefs = self.memory.get_preferences()
        routines = self.memory.list_routines()
        audit = self.actions.audit_log()

        partes = []
        if prefs:
            partes.append("=== PREFERENCIAS ===")
            for k, v in prefs.items():
                partes.append(f"{k} = {v}")
        if routines:
            partes.append("\\n=== RUTINAS ===")
            for r in routines:
                estado = "confirmada" if r.get("confirmed") else "pendiente"
                partes.append(f"{r['name']} — {r.get('description', '')} [{estado}]")
        if audit:
            partes.append("\\n=== ACCIONES RECIENTES ===")
            for entry in audit[-15:]:
                partes.append(f"{entry['time']} · {entry['action']} · {entry['detail']}")

        if not partes:
            self.ui.print_warning("No hay suficientes datos para sugerir ideas. Guarda algunas preferencias o usa Abril un poco más.")
            return True

        contexto = "\\n".join(partes[:MAX_PATTERN_CHARS])

        system_prompt = (
            "Eres un creador de ideas proactivo. Basándote en las preferencias, rutinas y acciones del usuario, "
            "propón 3-5 ideas concretas: proyectos que podría construir, mejoras a su flujo de trabajo, "
            "herramientas que podría instalar o automatizaciones que le ahorrarían tiempo. "
            "Presenta cada idea como una sugerencia (no una orden), con una breve justificación de por qué "
            "le podría convenir basándote en lo que ya sabes de él. Responde en español, tono alegre y juguetón."
        )

        self.ui.start_typing()
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conocimiento del usuario:\\n{contexto}"},
            ]
            answer = self.chat.provider.complete(messages)
            self.ui.stop_typing()
        except Exception as e:
            self.ui.stop_typing()
            self.ui.print_error(f"Error del modelo: {e}")
            return True

        self.ui.print_assistant(answer)
        return True

    # ── pensar ──
    def _cmd_pensar(self, args: list[str]) -> bool:
        if not args:
            self.ui.print_error("Uso: /pensar <tema o pregunta>")
            return True
        tema = " ".join(args)

        system_prompt = (
            "Eres un pensador profundo y reflexivo. Cuando el usuario te pide que pienses en algo, "
            "razona paso a paso: 1) descompón el tema en partes, 2) explora ventajas y desventajas, "
            "3) considera escenarios alternativos, 4) identifica riesgos y oportunidades, "
            "5) da una recomendación fundamentada. Siempre deja la decisión final al usuario. "
            "Responde en español, tono reflexivo pero accesible."
        )

        self.ui.start_typing()
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Tema para pensar: {tema}"},
            ]
            answer = self.chat.provider.complete(messages)
            self.ui.stop_typing()
        except Exception as e:
            self.ui.stop_typing()
            self.ui.print_error(f"Error del modelo: {e}")
            return True

        self.ui.print_assistant(answer)
        return True
