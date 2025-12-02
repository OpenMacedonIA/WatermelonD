import datetime
import json
import os

class ReminderManager:
    """Gestiona los recordatorios (medicación, citas, etc.)."""
    def __init__(self, data_file='reminders.json'):
        self.data_file = data_file
        self.reminders = self._load_reminders()

    def _load_reminders(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    reminders_data = json.load(f)
                    for r in reminders_data:
                        r['time'] = datetime.time.fromisoformat(r['time'])
                    return reminders_data
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def _save_reminders(self):
        with open(self.data_file, 'w') as f:
            serializable_reminders = [{**r, 'time': r['time'].isoformat()} for r in self.reminders]
            json.dump(serializable_reminders, f, indent=4)

    def add_medication_reminder(self, hour, minute, details, icon_id):
        """Añade un recordatorio de medicación diario."""
        new_reminder = {
            'type': 'medication',
            'time': datetime.time(hour, minute),
            'details': details,
            'icon_id': icon_id,
            'triggered_pre': False,
            'triggered_main': False,
            'last_triggered_date': None
        }
        self.reminders.append(new_reminder)
        self._save_reminders()

    def check_reminders(self, now):
        """Comprueba si algún recordatorio debe activarse y devuelve acciones."""
        actions = []
        current_time = now.time()
        current_date_str = now.date().isoformat()

        for reminder in self.reminders:
            # Resetea los flags diarios para que el recordatorio suene cada día
            if reminder.get('last_triggered_date') != current_date_str:
                reminder['triggered_pre'] = False
                reminder['triggered_main'] = False

            if not reminder.get('triggered_main'):
                # Pre-notificación 10 minutos antes
                pre_notify_time = (datetime.datetime.combine(now.date(), reminder['time']) - datetime.timedelta(minutes=10)).time()
                if current_time >= pre_notify_time and not reminder.get('triggered_pre'):
                    actions.append({'type': 'light_effect', 'effect': 'soft_pulse', 'color': 'blue'})
                    reminder['triggered_pre'] = True
                    reminder['last_triggered_date'] = current_date_str

                # Notificación principal a la hora exacta
                if current_time >= reminder['time']:
                    actions.append({'type': 'highlight_icon', 'icon_id': reminder['icon_id']})
                    actions.append({'type': 'sound', 'sound_name': 'clear_chime'})
                    actions.append({'type': 'speak', 'text': f"Es la hora de tu medicación: {reminder['details']}."})
                    reminder['triggered_main'] = True
                    # No guardamos aquí para no escribir en disco constantemente

        return actions