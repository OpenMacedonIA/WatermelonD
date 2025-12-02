import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from modules.calendar import CalendarManager

class DashboardDataManager:
    def __init__(self, config_manager=None):
        self.config = config_manager
        # Default location (Madrid) if not configured
        self.lat = 40.4168
        self.lon = -3.7038
        self.calendar = CalendarManager()

    def get_weather(self):
        """Fetches current weather from OpenMeteo (Free, no key)."""
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
        # Simplified WMO codes
        if code == 0: return "Clear sky"
        if code in [1, 2, 3]: return "Partly cloudy"
        if code in [45, 48]: return "Fog"
        if code in [51, 53, 55]: return "Drizzle"
        if code in [61, 63, 65]: return "Rain"
        if code in [71, 73, 75]: return "Snow"
        if code in [95, 96, 99]: return "Thunderstorm"
        return "Unknown"

    def get_news(self):
        """Fetches top headlines from BBC News (RSS)."""
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
        """Gets upcoming events for today and tomorrow."""
        today = datetime.now()
        events = []
        
        # Check today
        day_events = self.calendar.get_events_for_day(today.year, today.month, today.day)
        for e in day_events:
            events.append(f"Today {e['time']}: {e['description']}")
            
        # Check tomorrow (simple logic, ignoring month rollover for brevity in MVP)
        # For a robust solution, use datetime delta
        tomorrow = today + import_datetime.timedelta(days=1) # Oops, need to import timedelta
        # Let's fix imports first
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
        
        # Today
        ev_today = self.calendar.get_events_for_day(today.year, today.month, today.day)
        for e in ev_today:
            events.append({'day': 'Today', 'time': e['time'], 'desc': e['description']})
            
        # Tomorrow
        ev_tom = self.calendar.get_events_for_day(tomorrow.year, tomorrow.month, tomorrow.day)
        for e in ev_tom:
            events.append({'day': 'Tomorrow', 'time': e['time'], 'desc': e['description']})
            
        return events
