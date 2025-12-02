from . import BaseSkill
from datetime import datetime
import locale

class TimeDateSkill(BaseSkill):
    def decir_hora_fecha(self, command, response, **kwargs):
        now = datetime.now()
        # "Son las 18:30 del miércoles 25 de noviembre"
        fecha_str = now.strftime("Son las %H:%M del %A %d de %B.")
        self.speak(fecha_str)

    def decir_dia_semana(self, command, response, **kwargs):
        now = datetime.now()
        dia = now.strftime("%A")
        self.speak(f"{response} {dia}")
