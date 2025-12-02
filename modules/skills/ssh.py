from modules.skills import BaseSkill

class SSHSkill(BaseSkill):
    def connect(self, command, response, **kwargs):
        # "conecta con [alias]"
        alias = command.replace("conecta con", "").replace("conectar con", "").strip()
        
        if not alias:
            self.speak("No he entendido a qué servidor quieres conectar.")
            return

        self.speak(f"{response} Intentando conectar a {alias}...")
        success, msg = self.core.ssh_manager.connect(alias)
        self.speak(msg)

    def execute(self, command, response, **kwargs):
        # "ejecuta [cmd] en [alias]"
        # Parsing simple: split by " en "
        if " en " not in command:
            self.speak("Dime qué ejecutar y dónde. Ejemplo: ejecuta docker ps en producción.")
            return

        parts = command.split(" en ")
        cmd_to_run = parts[0].replace("ejecuta", "").strip()
        alias = parts[1].strip()

        self.speak(f"{response} Ejecutando '{cmd_to_run}' en {alias}...")
        success, output = self.core.ssh_manager.execute(alias, cmd_to_run)
        
        if success:
            # Limitar salida si es muy larga
            if len(output) > 200:
                self.speak("El comando se ejecutó correctamente. La salida es muy larga, te leo el final.")
                self.speak(output[-200:])
            else:
                self.speak(f"Resultado: {output}")
        else:
            self.speak(f"Hubo un error: {output}")

    def disconnect(self, command, response, **kwargs):
        alias = command.replace("desconecta de", "").strip()
        if not alias:
            self.speak("¿De qué servidor me desconecto?")
            return

        success, msg = self.core.ssh_manager.disconnect(alias)
        self.speak(msg)
