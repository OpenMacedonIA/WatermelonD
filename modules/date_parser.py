import re
from datetime import datetime, timedelta
# --- NUEVO: Importar la librería dateparser ---
try:
    # Usamos search_dates que es ideal para encontrar fechas dentro de un texto más largo
    from dateparser.search import search_dates
    DATEPARSER_AVAILABLE = True
except ImportError:
    search_dates = None
    DATEPARSER_AVAILABLE = False

def parse_reminder_from_text(text):
    """
    Analiza un texto para extraer la descripción, fecha y hora de un recordatorio.
    VERSIÓN MEJORADA con la librería dateparser.
    """
    if not DATEPARSER_AVAILABLE:
        # Si dateparser no está instalado, usamos la lógica original como respaldo.
        return _parse_reminder_from_text_original(text)

    # Buscamos fechas en español, prefiriendo fechas futuras.
    # 'search_dates' devuelve una lista de tuplas: (texto_encontrado, objeto_datetime)
    found_dates = search_dates(text, languages=['es'], settings={'PREFER_DATES_FROM': 'future'})

    if not found_dates:
        # --- MEJORA 1: Gestionar ambigüedad ---
        # Si no se encuentra fecha, no fallamos. Devolvemos la descripción
        # para que el asistente pueda preguntar "¿Para cuándo?".
        return {
            "status": "needs_date",
            "description": text.capitalize(),
            "date": None,
            "time": None
        }

    # Nos quedamos con la primera fecha encontrada
    date_text, reminder_datetime = found_dates[0]
    is_time_inferred = reminder_datetime.hour == 0 and reminder_datetime.minute == 0

    # La descripción es el texto original sin la parte de la fecha.
    description = text.replace(date_text, '').strip()

    return {
        "description": description.capitalize(),
        "date": reminder_datetime.strftime("%Y-%m-%d"),
        "time": reminder_datetime.strftime("%H:%M"),
        # --- MEJORA 2: Añadir un flag para saber si la hora fue especificada ---
        "time_inferred": is_time_inferred
    }

def _parse_reminder_from_text_original(text):
    """Lógica original de parseo manual como fallback."""
    text = text.lower()
    
    # --- Mapeos de texto a valores ---
    days_of_week = {
        "lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3,
        "viernes": 4, "sábado": 5, "domingo": 6
    }
    months = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }

    # --- Expresiones Regulares para encontrar patrones ---
    # "a las 14:30", "a las 2"
    time_pattern = re.search(r'a las (\d{1,2}(?::\d{2})?)', text)
    # "el 15 de octubre"
    date_pattern = re.search(r'el (\d{1,2}) de (\w+)', text)
    # "el martes", "el próximo lunes"
    day_of_week_pattern = re.search(r'el (próximo )?(\w+)', text)

    reminder_date = None
    reminder_time = "09:00" # Hora por defecto si no se especifica
    description = text

    # 1. Extraer la hora
    if time_pattern:
        time_str = time_pattern.group(1)
        if ":" not in time_str:
            time_str += ":00" # Completa '14' a '14:00'
        reminder_time = f"{int(time_str.split(':')[0]):02d}:{int(time_str.split(':')[1]):02d}"
        # Eliminar la parte de la hora de la descripción
        description = description.replace(time_pattern.group(0), "").strip()

    # 2. Extraer la fecha
    if date_pattern:
        day = int(date_pattern.group(1))
        month_name = date_pattern.group(2)
        if month_name in months:
            month = months[month_name]
            year = datetime.now().year
            # Si la fecha ya ha pasado este año, asumimos que es del año que viene
            if datetime(year, month, day) < datetime.now():
                year += 1
            reminder_date = datetime(year, month, day)
            description = description.replace(date_pattern.group(0), "").strip()

    elif day_of_week_pattern:
        day_name = day_of_week_pattern.group(2)
        if day_name in days_of_week:
            today = datetime.now()
            target_weekday = days_of_week[day_name]
            days_ahead = target_weekday - today.weekday()
            if days_ahead <= 0: # Si es hoy o un día pasado de la semana, ir a la semana siguiente
                days_ahead += 7
            reminder_date = today + timedelta(days=days_ahead)
            description = description.replace(day_of_week_pattern.group(0), "").strip()

    # Si no se encontró fecha, no podemos crear el recordatorio
    if not reminder_date:
        return None

    # Limpiar la descripción de palabras de relleno
    description = description.replace("que tengo", "").replace("es el", "").strip()
    if not description:
        return None

    return {
        "description": description.capitalize(),
        "date": reminder_date.strftime("%Y-%m-%d"),
        "time": reminder_time
    }

def parse_alarm_from_text(text):
    """
    Analiza un texto para extraer la hora, los días y la etiqueta de una alarma.
    """
    text = text.lower()
    
    days_map = {
        "lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3,
        "viernes": 4, "sábado": 5, "domingo": 6
    }
    
    alarm_time = None
    alarm_days = []
    alarm_label = "Alarma"

    # 1. Extraer la hora (ej: "a las 7", "a las 8 y media", "a las 14:30")
    time_match = re.search(r'a las (\d{1,2})(:(\d{2}))?( y media)?', text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(3)) if time_match.group(3) else 0
        if time_match.group(4): # "y media"
            minute = 30
        alarm_time = (hour, minute)

    # 2. Extraer los días de la semana
    found_days = False
    for day_name, day_index in days_map.items():
        if day_name in text:
            alarm_days.append(day_index)
            found_days = True
    
    if "todos los días" in text:
        alarm_days = list(range(7))
        found_days = True

    # Si no se especifican días, se asume que es para todos los días
    if not found_days:
        alarm_days = list(range(7))

    # 3. Extraer etiqueta (opcional)
    label_match = re.search(r'con la etiqueta (.+)', text)
    if label_match:
        alarm_label = label_match.group(1).strip()

    if alarm_time:
        return {"time": alarm_time, "days": alarm_days, "label": alarm_label.capitalize()}
    return None
    
