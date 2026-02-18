import datetime
import json
import os
from collections import defaultdict

class CalendarManager:
    """Gestiona eventos del calendario."""
    def __init__(self, data_file='calendar.json'):
        self.data_file = data_file
        self.events = self._load_events()

    def _load_events(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def _save_events(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.events, f, indent=4)

    def add_event(self, year, month, day, hour, minute, description):
        """Añade un nuevo evento."""
        event_date = f"{year:04d}-{month:02d}-{day:02d}"
        event_time = f"{hour:02d}:{minute:02d}"
        new_event = {
            'date': event_date,
            'time': event_time,
            'description': description
        }
        self.events.append(new_event)
        self._save_events()

    def get_events_for_month(self, year, month):
        """Devuelve un diccionario de eventos para un mes, agrupados por día."""
        month_str = f"{year:04d}-{month:02d}"
        events_in_month = defaultdict(list)
        for event in self.events:
            if event['date'].startswith(month_str):
                day = int(event['date'].split('-')[2])
                events_in_month[day].append(event)
        return events_in_month

    def get_events_for_day(self, year, month, day):
        """Devuelve una lista de eventos para un día específico."""
        day_str = f"{year:04d}-{month:02d}-{day:02d}"
        return [event for event in self.events if event['date'] == day_str]

    def get_events_summary_for_day(self, day_es):
        """
        Busca eventos para un día específico de la semana y devuelve un resumen en texto.
        """
        day_es_lower = day_es.lower()
        day_map = {
            "lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3,
            "viernes": 4, "sábado": 5, "domingo": 6
        }
        if day_es_lower not in day_map:
            return "No he entendido el día."

        today = datetime.date.today()
        target_weekday = day_map[day_es_lower]
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0: days_ahead += 7
        target_date = today + datetime.timedelta(days=days_ahead)
        target_date_str = target_date.strftime("%Y-%m-%d")

        events_on_day = [e for e in self.events if e['date'] == target_date_str]
        if not events_on_day:
            return f"No tienes nada programado para el {day_es}."

        summary_parts = [f"a las {e['time']}, tienes {e['description']}" for e in sorted(events_on_day, key=lambda x: x['time'])]
        return f"el {day_es}, " + "; ".join(summary_parts)