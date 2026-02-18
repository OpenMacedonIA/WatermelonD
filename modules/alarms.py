import datetime
import json
import os
import logging
from modules.config_manager import ConfigManager

class AlarmManager:
    """Gestiona las alarmas."""
    def __init__(self, data_file=None):
        if data_file is None:
            data_file = ConfigManager().get('paths', {}).get('alarms', 'jsons/alarms.json')
        self.data_file = data_file
        self.alarms = self._load_alarms()

    def _load_alarms(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                logging.error("Error al cargar el fichero de alarmas, se creará uno nuevo.")
                return []
        return []

    def _save_alarms(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.alarms, f, indent=4, ensure_ascii=False)

    def add_alarm(self, hour, minute, days_of_week, label="Alarma"):
        """Añade una alarma. days_of_week: lista de enteros (0=Lunes, 6=Domingo)."""
        new_alarm = {
            'time': f"{hour:02d}:{minute:02d}",
            'days_of_week': days_of_week,
            'label': label,
            'last_triggered_date': None
        }
        self.alarms.append(new_alarm)
        self._save_alarms()
        logging.info(f"Alarma añadida: {label} a las {new_alarm['time']} los días {days_of_week}")

    def delete_alarm(self, alarm_to_delete):
        """Elimina una alarma de la lista."""
        # Comparamos por contenido, no por instancia de objeto
        self.alarms = [alarm for alarm in self.alarms if alarm != alarm_to_delete]
        self._save_alarms()
        logging.info(f"Alarma eliminada: {alarm_to_delete.get('label')} a las {alarm_to_delete.get('time')}")
    def get_all_alarms(self):
        return self.alarms

    def get_alarms_summary(self):
        """Genera un resumen en texto de todas las alarmas programadas."""
        if not self.alarms:
            return "No tienes ninguna alarma programada."

        days_map = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
        summary_parts = []

        for alarm in self.alarms:
            time = alarm['time']
            label = alarm['label']
            days = alarm['days_of_week']

            if len(days) == 7:
                days_str = "todos los días"
            else:
                days_str = "los " + ", ".join([days_map[d] for d in sorted(days)])
            
            summary_parts.append(f"{label} a las {time} {days_str}")
        
        return "; ".join(summary_parts)

    def check_alarms(self, now):
        """Comprueba si alguna alarma debe sonar y devuelve acciones."""
        actions = []
        current_time_str = now.strftime("%H:%M")
        current_date_str = now.date().isoformat()
        today_weekday = now.weekday() # Lunes es 0

        for alarm in self.alarms:
            if today_weekday in alarm['days_of_week'] and alarm['time'] == current_time_str:
                if alarm.get('last_triggered_date') != current_date_str:
                    actions.append({'type': 'speak', 'text': f"Son las {alarm['time']}, recordatorio de alarma: {alarm['label']}"})
                    alarm['last_triggered_date'] = current_date_str
                    self._save_alarms() # Guardar para no repetir hoy
        return actions