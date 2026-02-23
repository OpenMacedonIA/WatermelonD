import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from modules.calendar_manager import CalendarManager

class DashboardDataManager:
    def __init__(self, config_manager=None):
        self.config = config_manager
        # Ubicación por defecto (Madrid) si no está configurada
        self.lat = 40.4168
        self.lon = -3.7038
        self.calendar = CalendarManager()

    def get_weather(self):
        """Obtiene el clima actual de OpenMeteo (Gratis, sin clave)."""
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current=temperature_2m,weather_code&timezone=auto"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                current = data.get('current', {})
                return {
                    'temp': current.get('temperature_2m', '--'),
                    'code': current.get('weather_code', 0),
                    'desc': self._get_weather_desc(current.get('weather_code', 0))
                }
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return {'temp': '--', 'code': 0, 'desc': 'Unavailable'}

    def _get_weather_desc(self, code):
        # Códigos WMO simplificados
        if code == 0: return "Cielo despejado"
        if code in [1, 2, 3]: return "Parcialmente nublado"
        if code in [45, 48]: return "Niebla"
        if code in [51, 53, 55]: return "Llovizna"
        if code in [61, 63, 65]: return "Lluvia"
        if code in [71, 73, 75]: return "Nieve"
        if code in [95, 96, 99]: return "Tormenta"
        return "Desconocido"

    def get_news(self):
        """Obtiene las noticias principales de BBC News (RSS)."""
        try:
            url = "http://feeds.bbci.co.uk/news/world/rss.xml"
            with urllib.request.urlopen(url, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                items = []
                for item in root.findall('.//item')[:5]:
                    title = item.find('title').text
                    items.append(title)
                return items
        except Exception as e:
            print(f"Error fetching news: {e}")
            return ["News unavailable"]

    def get_calendar_summary(self):
        """Obtiene próximos eventos para hoy y mañana."""
        today = datetime.now()
        events = []
        
        # Comprobar hoy
        day_events = self.calendar.get_events_for_day(today.year, today.month, today.day)
        for e in day_events:
            events.append(f"Hoy {e['time']}: {e['description']}")
            
        # Comprobar mañana (lógica simple, ignorando cambio de mes para mayor brevedad en MVP)
        # Para una solución robusta, usar datetime delta
        tomorrow = today + import_datetime.timedelta(days=1) # Ups, necesito importar timedelta
        # Vamos a arreglar las importaciones primero
        return events

    def get_all_data(self):
        return {
            'weather': self.get_weather(),
            'news': self.get_news(),
            'calendar': self.get_calendar_summary_robust()
        }

    def get_calendar_summary_robust(self):
        from datetime import timedelta
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        events = []
        
        # Hoy
        ev_today = self.calendar.get_events_for_day(today.year, today.month, today.day)
        for e in ev_today:
            events.append({'day': 'Hoy', 'time': e['time'], 'desc': e['description']})
            
        # Mañana
        ev_tom = self.calendar.get_events_for_day(tomorrow.year, tomorrow.month, tomorrow.day)
        for e in ev_tom:
            events.append({'day': 'Mañana', 'time': e['time'], 'desc': e['description']})
            
        return events
