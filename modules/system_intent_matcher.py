"""
SystemIntentMatcher — Pre-Router de Comandos de Sistema
=========================================================
Se ejecuta ANTES del router categorizador (DecisionRouter).
Compara la entrada del usuario con los intents definidos en
config/system_intents.json y, si hay coincidencia, ejecuta
la skill vinculada directamente, descartando el router.

Categorías gestionadas:
  - power    : apagar / reiniciar
  - volume   : subir / bajar / silenciar / porcentaje
  - alarm    : crear / listar alarmas
  - timer    : crear temporizador
  - calendar : ver agenda (hoy / fecha específica)
"""

import re
import os
import json
import logging
from typing import Optional, Dict, Tuple


logger = logging.getLogger("SystemIntentMatcher")

# Lógica difusa (mismo patrón que IntentManager)
try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
    logger.info("RapidFuzz disponible — SystemIntentMatcher usará matching difuso.")
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("RapidFuzz no instalado — SystemIntentMatcher usará solo matching exacto.")


class SystemIntentMatcher:
    """
    Detecta intents de sistema y ejecuta la acción correspondiente
    sin pasar por el router categorizador.

    Uso:
        matcher = SystemIntentMatcher(core)
        handled = matcher.process(command_text)
        if handled:
            return  # El comando fue gestionado, no enviar al router
    """

    INTENTS_PATH = "config/system_intents.json"

    def __init__(self, core_instance):
        self.core = core_instance
        self.intents = self._load_intents()
        # Pre-calcular mapa trigger → intent para búsqueda O(1) en modo exacto
        # y lista plana de triggers para RapidFuzz
        self._trigger_map: Dict[str, Dict] = {}
        self._triggers_list = []
        for intent in self.intents:
            for trigger in intent.get("triggers", []):
                self._trigger_map[trigger] = intent
        self._triggers_list = list(self._trigger_map.keys())

        logger.info(
            f"SystemIntentMatcher inicializado con {len(self.intents)} intents, "
            f"{len(self._triggers_list)} triggers, "
            f"modo={'difuso+exacto' if RAPIDFUZZ_AVAILABLE else 'exacto'}."
        )

    # ------------------------------------------------------------------ #
    #  Carga                                                               #
    # ------------------------------------------------------------------ #

    def _load_intents(self):
        """Carga los intents desde el JSON de configuración."""
        path = self.INTENTS_PATH
        if not os.path.exists(path):
            logger.error(f"No se encontró el fichero de intents: {path}")
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            intents = data.get("intents", [])
            logger.info(f"Cargados {len(intents)} system intents desde {path}")
            return intents
        except Exception as e:
            logger.error(f"Error cargando {path}: {e}")
            return []

    def _get_categories(self):
        return {i.get("category", "unknown") for i in self.intents}

    # ------------------------------------------------------------------ #
    #  Match — Exacto + Difuso (RapidFuzz)                                 #
    # ------------------------------------------------------------------ #

    def _find_intent(self, command: str) -> Optional[Dict]:
        """
        Busca el intent más apropiado para el comando usando tres niveles:

        Nivel 1 — Substring exacto (O(n), velocidad máxima):
            Si cualquier trigger está contenido literalmente en el comando → match
            Ejemplo: "pon un temporizador" contiene trigger "pon un temporizador de"
            Nota: solo si el trigger es parte del comando

        Nivel 2 — RapidFuzz token_sort_ratio ≥ 82:
            Ignora orden de palabras y palabras extra.
            "sube el volumen un poco" → match con "sube el volumen" (82+)

        Nivel 3 — RapidFuzz partial_ratio con penalización de longitud ≥ 75:
            Para frases cortas/parciales como "silencio" o "apaga".
            Penaliza fuertemente diferencias de longitud para evitar falsos positivos.
        """
        command_lower = command.lower().strip()

        # ── Nivel 1: Substring exacto ─────────────────────────────────
        for trigger, intent in self._trigger_map.items():
            if trigger in command_lower:
                logger.info(f"[MATCH-EXACTO] '{trigger}' en '{command_lower}'")
                return intent

        # ── Nivel 2 y 3: RapidFuzz (si disponible) ───────────────────
        if not RAPIDFUZZ_AVAILABLE or not self._triggers_list:
            return None

        # Nivel 2 — token_sort_ratio (tolerante al orden)
        match_ts = process.extractOne(
            command_lower,
            self._triggers_list,
            scorer=fuzz.token_sort_ratio
        )
        if match_ts:
            ts_trigger, ts_score, _ = match_ts
            if ts_score >= 82:
                intent = self._trigger_map[ts_trigger]
                logger.info(
                    f"[MATCH-FUZZY-TS] '{command_lower}' ≈ '{ts_trigger}' "
                    f"(score={ts_score}, intent={intent.get('name')})"
                )
                return intent

            # Nivel 3 — partial_ratio + penalización de longitud
            if ts_score >= 60:
                match_pr = process.extractOne(
                    command_lower,
                    self._triggers_list,
                    scorer=fuzz.partial_ratio
                )
                if match_pr:
                    pr_trigger, pr_score, _ = match_pr
                    len_diff = abs(len(command_lower) - len(pr_trigger))
                    # Penalización por diferencia de longitud (evita falsos positivos)
                    penalty = 15 if len_diff > 5 else 0
                    final_score = pr_score - penalty

                    if final_score >= 75:
                        intent = self._trigger_map[pr_trigger]
                        logger.info(
                            f"[MATCH-FUZZY-PR] '{command_lower}' ≈ '{pr_trigger}' "
                            f"(raw={pr_score}, pen={penalty}, final={final_score}, "
                            f"intent={intent.get('name')})"
                        )
                        return intent

        return None

    def _extract_context(self, command: str, extractors: Dict[str, str]) -> Dict[str, str]:
        """Extrae variables de contexto del comando mediante regex."""
        context = {}
        for var, pattern in extractors.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                value = next((g for g in match.groups() if g is not None), None)
                if value:
                    context[var] = value.strip()
        return context

    # ------------------------------------------------------------------ #
    #  Entry point principal                                               #
    # ------------------------------------------------------------------ #

    def process(self, command_text: str) -> bool:
        """
        Evalúa el comando y ejecuta la skill correspondiente si hay match.

        Returns:
            True  → el comando fue gestionado (no debe enviarse al router)
            False → no hay match en ningún nivel, continuar con el flujo normal

        IMPORTANTE: Si el intent ES detectado, SIEMPRE se gestiona aquí aunque
        no se pueda extraer contexto. El handler pedirá los datos al usuario.
        Esto evita que el router reciba comandos de sistema y los malinterprete.
        """
        intent = self._find_intent(command_text)
        if not intent:
            return False

        # Intentar extraer contexto si el intent lo requiere
        context = {}
        if intent.get("requires_context"):
            extractors = intent.get("context_extractors", {})
            context = self._extract_context(command_text, extractors)

            # OJO: si no hay contexto, NO abandonamos al router.
            # El handler correspondiente preguntará al usuario.
            if not context:
                logger.info(
                    f"Intent '{intent['name']}' matchado sin contexto extraído — "
                    f"handler pedirá los datos al usuario."
                )

        action = intent.get("action", "")
        category = intent.get("category", "unknown")

        logger.info(f"[SystemIM] Acción '{action}' (cat={category}, ctx={context})")

        try:
            dispatched = self._dispatch(action, command_text, context)
            if dispatched:
                return True
            # Si _dispatch no encontró handler, avisar pero consumir igualmente
            logger.warning(f"[SystemIM] Acción '{action}' sin handler registrado.")
            return True  # Consumido para no mandar al router
        except Exception as e:
            logger.error(f"[SystemIM] Error en acción '{action}': {e}", exc_info=True)
            self.core.speak("Ha ocurrido un error ejecutando ese comando de sistema.")
            return True  # Consumido aunque con error

    # ------------------------------------------------------------------ #
    #  Dispatcher                                                          #
    # ------------------------------------------------------------------ #

    # Tabla action → nombre de método (resuelto con getattr para evitar
    # referencias a self en el cuerpo de la clase que confunden a Pyre).
    _ACTION_MAP = {
        "system_shutdown":  "_handle_shutdown",
        "system_reboot":    "_handle_reboot",
        "volume_up":        "_handle_volume_up",
        "volume_down":      "_handle_volume_down",
        "volume_mute":      "_handle_volume_mute",
        "volume_set":       "_handle_volume_set",
        "alarm_create":     "_handle_alarm_create",
        "alarm_list":       "_handle_alarm_list",
        "timer_create":     "_handle_timer_create",
        "calendar_today":   "_handle_calendar_today",
        "calendar_date":    "_handle_calendar_date",
        # Datetime — interceptados para evitar carga del LLM
        "datetime_time":    "_handle_datetime_time",
        "datetime_date":    "_handle_datetime_date",
        "datetime_weekday": "_handle_datetime_weekday",
    }

    def _dispatch(self, action: str, command: str, context: Dict) -> bool:
        """Mapea la acción al método correspondiente usando _ACTION_MAP."""
        method_name = self._ACTION_MAP.get(action)
        if method_name:
            handler = getattr(self, method_name)
            handler(command, context)
            return True

        logger.warning(f"No existe handler para la acción '{action}'")
        return False

    # ------------------------------------------------------------------ #
    #  Handlers — POWER                                                    #
    # ------------------------------------------------------------------ #

    def _handle_shutdown(self, command: str, context: Dict):
        self.core.speak("Entendido. Apagando el sistema en 5 segundos.")
        logger.info("Acción: APAGAR SISTEMA")

        if self.core.sysadmin_manager:
            self.core.sysadmin_manager.run_command("sudo shutdown -h +0")
        else:
            # Fallback: cerrar NeoCore limpiamente
            import threading
            threading.Timer(2, self.core.on_closing).start()

    def _handle_reboot(self, command: str, context: Dict):
        self.core.speak("De acuerdo. Reiniciando el sistema.")
        logger.info("Acción: REINICIAR SISTEMA")

        if self.core.sysadmin_manager:
            self.core.sysadmin_manager.run_command("sudo reboot")
        else:
            import subprocess
            subprocess.Popen(["sudo", "reboot"])

    # ------------------------------------------------------------------ #
    #  Handlers — VOLUME                                                   #
    # ------------------------------------------------------------------ #

    def _set_volume_pactl(self, delta: str) -> Tuple[bool, str]:
        """Ejecuta pactl para ajustar el volumen del sumidero por defecto."""
        import subprocess
        try:
            result = subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", delta],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0, result.stderr.strip()
        except FileNotFoundError:
            # pactl no disponible, intentar amixer
            try:
                cmd = f"amixer set Master {delta}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                return result.returncode == 0, result.stderr.strip()
            except Exception as e:
                return False, str(e)
        except Exception as e:
            return False, str(e)

    def _handle_volume_up(self, command: str, context: Dict):
        ok, err = self._set_volume_pactl("+10%")
        if ok:
            self.core.speak("Subiendo el volumen.")
        else:
            logger.error(f"Error subiendo volumen: {err}")
            self.core.speak("No he podido ajustar el volumen.")

    def _handle_volume_down(self, command: str, context: Dict):
        ok, err = self._set_volume_pactl("-10%")
        if ok:
            self.core.speak("Bajando el volumen.")
        else:
            logger.error(f"Error bajando volumen: {err}")
            self.core.speak("No he podido ajustar el volumen.")

    def _handle_volume_mute(self, command: str, context: Dict):
        import subprocess
        try:
            result = subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.core.speak("Silenciando el sistema.")
            else:
                self.core.speak("No he podido silenciar el audio.")
        except FileNotFoundError:
            # Fallback amixer
            import subprocess
            subprocess.run("amixer set Master toggle", shell=True)
            self.core.speak("Silenciado.")
        except Exception as e:
            logger.error(f"Error al silenciar: {e}")
            self.core.speak("No he podido silenciar el audio.")

    def _handle_volume_set(self, command: str, context: Dict):
        level = context.get("level", "50")
        ok, err = self._set_volume_pactl(f"{level}%")
        if ok:
            self.core.speak(f"Volumen ajustado al {level} por ciento.")
        else:
            logger.error(f"Error ajustando volumen: {err}")
            self.core.speak(f"No he podido poner el volumen al {level} por ciento.")

    # ------------------------------------------------------------------ #
    #  Handlers — ALARM                                                    #
    # ------------------------------------------------------------------ #

    def _parse_time_string(self, time_str: str) -> Optional[Tuple[int, int]]:
        """
        Convierte un string de hora natural en (hora, minuto).
        Soporta: '8', '8:30', '8 de la mañana', '14:00', '3 de la tarde', etc.
        """
        time_str = time_str.lower().strip()

        # Determinar si es PM por contexto
        is_pm = any(kw in time_str for kw in ["de la tarde", "de la noche", "pm"])
        is_am = any(kw in time_str for kw in ["de la mañana", "am"])

        # Limpiar textos adicionales
        clean = re.sub(r"de la (mañana|tarde|noche)|am|pm", "", time_str).strip()

        # Intentar parsear HH:MM
        match_hhmm = re.match(r"^(\d{1,2}):(\d{2})$", clean)
        if match_hhmm:
            h, m = int(match_hhmm.group(1)), int(match_hhmm.group(2))
        else:
            match_h = re.match(r"^(\d{1,2})$", clean)
            if match_h:
                h, m = int(match_h.group(1)), 0
            else:
                return None

        # Corrección AM/PM
        if is_pm and h < 12:
            h += 12
        if is_am and h == 12:
            h = 0

        # Validar rango
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m

        return None

    def _handle_alarm_create(self, command: str, context: Dict):
        time_str = context.get("time", "")
        parsed = self._parse_time_string(time_str)

        if not parsed:
            # Activar el diálogo de espera de hora
            self.core.speak(
                "¿A qué hora quieres la alarma? Dímelo como, por ejemplo, ocho de la mañana."
            )
            self.core.waiting_for_alarm_confirmation = True
            self.core.pending_alarm_data = {"time_str": time_str}
            return

        hour, minute = parsed
        # Crear alarma todos los días por defecto
        self.core.alarm_manager.add_alarm(
            hour=hour,
            minute=minute,
            days_of_week=list(range(7)),
            label=f"Alarma {hour:02d}:{minute:02d}"
        )
        self.core.speak(
            f"Alarma configurada para las {hour:02d}:{minute:02d}. ¡No falles!"
        )
        logger.info(f"Alarma creada: {hour:02d}:{minute:02d}")

    def _handle_alarm_list(self, command: str, context: Dict):
        if not self.core.alarm_manager:
            self.core.speak("El gestor de alarmas no está disponible.")
            return

        summary = self.core.alarm_manager.get_alarms_summary()
        self.core.speak(summary)

    # ------------------------------------------------------------------ #
    #  Handlers — TIMER                                                    #
    # ------------------------------------------------------------------ #

    def _parse_duration_seconds(self, duration_str: str) -> int:
        """Convierte '10 minutos', '30 segundos', '2 horas' a segundos."""
        duration_str = duration_str.lower().strip()
        number_match = re.search(r"(\d+)", duration_str)
        if not number_match:
            return 0
        value = int(number_match.group(1))

        if any(kw in duration_str for kw in ["hora", "h"]):
            return value * 3600
        if any(kw in duration_str for kw in ["minuto", "min"]):
            return value * 60
        if any(kw in duration_str for kw in ["segundo", "seg"]):
            return value

        return value * 60  # Por defecto: minutos

    def _handle_timer_create(self, command: str, context: Dict):
        duration_str = context.get("duration", "")
        seconds = self._parse_duration_seconds(duration_str)

        if seconds <= 0:
            self.core.speak("¿Cuánto tiempo quieres? Dímelo, por ejemplo, diez minutos.")
            self.core.waiting_for_timer_duration = True
            return

        # Humanizar duración
        if seconds >= 3600:
            human = f"{seconds // 3600} hora{'s' if seconds // 3600 > 1 else ''}"
        elif seconds >= 60:
            human = f"{seconds // 60} minuto{'s' if seconds // 60 > 1 else ''}"
        else:
            human = f"{seconds} segundo{'s' if seconds > 1 else ''}"

        self.core.speak(f"Temporizador de {human} en marcha. ¡Tic-tac!")
        logger.info(f"Temporizador: {seconds}s")

        from datetime import datetime, timedelta
        self.core.active_timer_end_time = datetime.now() + timedelta(seconds=seconds)
        # NeoCore._check_frequent_tasks() detecta active_timer_end_time cada segundo
        # y avisa al usuario. NO lanzar un thread adicional o habrá doble aviso.
        logger.info(f"[TIMER] active_timer_end_time fijado en {self.core.active_timer_end_time} (+{seconds}s)")

    # ------------------------------------------------------------------ #
    #  Handlers — CALENDAR                                                 #
    # ------------------------------------------------------------------ #

    def _handle_calendar_today(self, command: str, context: Dict):
        if not self.core.calendar_manager:
            self.core.speak("El gestor de calendario no está disponible.")
            return

        from datetime import datetime
        now = datetime.now()
        events = self.core.calendar_manager.get_events_for_day(now.year, now.month, now.day)

        if not events:
            self.core.speak("No tienes ningún evento en la agenda para hoy.")
            return

        count = len(events)
        self.core.speak(f"Tienes {count} evento{'s' if count > 1 else ''} hoy.")

        for ev in events[:3]:  # Leer máximo 3 para no ser pesado por voz
            desc = ev.get("description", "Sin descripción")
            time_str = ev.get("time", "")
            if time_str:
                self.core.speak(f"A las {time_str}: {desc}.")
            else:
                self.core.speak(f"{desc}.")

        if count > 3:
            self.core.speak(f"Y {count - 3} evento{'s' if count - 3 > 1 else ''} más.")

    def _handle_calendar_date(self, command: str, context: Dict):
        if not self.core.calendar_manager:
            self.core.speak("El gestor de calendario no está disponible.")
            return

        date_str = context.get("date", "").lower().strip()
        from datetime import datetime, timedelta

        now = datetime.now()

        # Resolver fecha relativa
        if date_str == "mañana":
            target = now + timedelta(days=1)
        elif date_str == "pasado mañana":
            target = now + timedelta(days=2)
        else:
            # Intentar resolver día de la semana
            weekdays_es = {
                "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
                "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
            }
            if date_str in weekdays_es:
                target_wd = weekdays_es[date_str]
                days_ahead = (target_wd - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target = now + timedelta(days=days_ahead)
            else:
                # Fecha numérica — no implementada en este handler básico
                self.core.speak(
                    f"No he podido interpretar la fecha '{date_str}'. "
                    f"Prueba diciéndome 'mañana' o un día de la semana."
                )
                return

        events = self.core.calendar_manager.get_events_for_day(
            target.year, target.month, target.day
        )
        day_label = target.strftime("%A %d de %B")

        if not events:
            self.core.speak(f"No tienes eventos el {day_label}.")
            return

        count = len(events)
        self.core.speak(f"El {day_label} tienes {count} evento{'s' if count > 1 else ''}.")
        for ev in events[:3]:
            desc = ev.get("description", "Sin descripción")
            time_str = ev.get("time", "")
            if time_str:
                self.core.speak(f"A las {time_str}: {desc}.")
            else:
                self.core.speak(f"{desc}.")

    # ------------------------------------------------------------------ #
    #  Handlers — DATETIME (hora / fecha / día)                            #
    # ------------------------------------------------------------------ #

    def _handle_datetime_time(self, command: str, context: Dict):
        """Responde la hora actual directamente sin pasar por el LLM."""
        from datetime import datetime
        import random

        now = datetime.now()
        hora = now.strftime("%H:%M")
        hora_hablada = now.strftime("%-H y %M minutos") if now.minute != 0 else now.strftime("%-H en punto")

        # Variedad de respuestas coloquiales
        respuestas = [
            f"Son las {hora_hablada}.",
            f"Ahora mismo son las {hora}.",
            f"Pues son las {hora_hablada}, colega.",
            f"Mira el reloj, vago... Es broma, son las {hora_hablada}.",
            f"Las {hora_hablada} en el reloj del sistema.",
        ]
        self.core.speak(random.choice(respuestas))
        logger.info(f"[DATETIME] Hora respondida: {hora} (sin LLM)")

    def _handle_datetime_date(self, command: str, context: Dict):
        """Responde la fecha actual directamente sin pasar por el LLM."""
        from datetime import datetime
        import random
        import locale

        now = datetime.now()
        # Intentar formato localizado
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except Exception:
            pass

        fecha = now.strftime("%A, %d de %B de %Y")
        fecha_corta = now.strftime("%d/%m/%Y")

        respuestas = [
            f"Hoy es {fecha}.",
            f"Estamos a {fecha}.",
            f"Hoy es {fecha}, para que no te pierdas.",
            f"La fecha de hoy es {fecha_corta}.",
        ]
        self.core.speak(random.choice(respuestas))
        logger.info(f"[DATETIME] Fecha respondida: {fecha} (sin LLM)")

    def _handle_datetime_weekday(self, command: str, context: Dict):
        """Responde el día de la semana directamente sin pasar por el LLM."""
        from datetime import datetime
        import random
        import locale

        now = datetime.now()
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except Exception:
            pass

        dia = now.strftime("%A").capitalize()

        respuestas = [
            f"Hoy es {dia}.",
            f"Estamos en {dia}.",
            f"{dia}, por si no tenías el calendario a mano.",
        ]
        self.core.speak(random.choice(respuestas))
        logger.info(f"[DATETIME] Día de semana respondido: {dia} (sin LLM)")

