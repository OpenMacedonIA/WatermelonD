import sys
import os

# Asegurar que podemos importar desde el directorio actual
sys.path.append(os.getcwd())

from test_lime_interactive import LimeTester

def run_tests():
    print("--- [LIME] INICIANDO CARGA DEL MODELO ---")
    tester = LimeTester()
    if not tester.load_model():
        print("[ERROR] Error cargando el modelo.")
        return

    # ==========================================
    # CONTEXTO DIFÍCIL (NeoCore - Lleno de ruido Python)
    # ==========================================
    ctx_neocore = [
        'changelog.md', 'config', 'data', 'database', 'debug_stt_standalone.py', 
        'modules', 'public_docs', 'resources', 'run_neocore_distrobox.sh', 'source', 
        'start.sh', 'start_services.py', 'TangerineUI', 'NeoCore.py', 'README.md', 
        'install.sh', 'requirements.txt', 'setup_distrobox.sh', 'setup_repos.sh', 
        'tests', 'logs', 'priv_docs', 'models', 'tts_cache', 'test_lime_interactive.py'
    ]

    # Pruebas específicas para ver si ignora el ruido y obedece comandos de sistema
    pruebas_neocore = [
        # ---  DOCKER (¿Sabe ignorar los .py?) ---
        "Despliega un contenedor redis en el puerto 6379",
        "Listame los contenedores activos",
        "Muestra los logs del contenedor llamado 'database'",
        "Para todos los contenedores que esten corriendo",
        "Ejecuta una terminal bash dentro del contenedor 'neocore_app'",

        # ---  NAVEGACIÓN Y ARCHIVOS (¿Sabe moverse?) ---
        "Entra en el directorio TangerineUI",
        "Sube un nivel de directorio",
        "Dime la ruta actual (pwd)",  # A ver si aquí no dice 'echo'
        "Busca el archivo 'settings.yaml' dentro de la carpeta config",
        "Muestrame las ultimas 10 lineas del changelog.md",
        "Cuenta cuantos archivos hay en la carpeta modules",

        # ---  ESTADO DEL SISTEMA (¿Sabe mirar el hardware?) ---
        "Verifica el espacio libre en disco",
        "Dime cuanta memoria RAM se esta usando",
        "Muestrame los puertos que estan escuchando en el sistema",
        "Reinicia el servicio de red"
    ]

    # ==========================================
    # CONTEXTO VACÍO (SysAdmin Puro)
    # ==========================================
    # Aquí no hay archivos que le distraigan. Debería ser 100% efectivo.
    pruebas_limpias = [
        "Actualiza los repositorios del sistema", # Debería usar dnf (Fedora)
        "Busca todos los archivos .log en /var/log",
        "Crea un usuario llamado 'admin' en el sistema",
        "Comprime la carpeta /home/user en un archivo tar.gz",
        "Mata el proceso con PID 1234"
    ]

    # ==========================================
    # BUCLE DE EJECUCIÓN
    # ==========================================
    print("\n---  INICIANDO BATERÍA DE PRUEBAS SYSADMIN ---")

    # 1. Ejecutar pruebas con ruido (NeoCore)
    print("\n---   GRUPO DE PRUEBAS 1: CONTEXTO NEOCORE (RUIDOSO) ---")
    for req in pruebas_neocore:
        print(f" Contexto: NeoCore | Solicitud > {req}")
        # Adaptación para usar la clase LimeTester
        tester.infer(req, context_override=ctx_neocore)
        

    # 2. Ejecutar pruebas limpias
    print("\n--- 🧹 GRUPO DE PRUEBAS 2: CONTEXTO LIMPIO (SYSADMIN) ---")
    for req in pruebas_limpias:
        print(f" Contexto: []      | Solicitud > {req}")
        tester.infer(req, context_override=[])

if __name__ == "__main__":
    run_tests()
