import sys
import os
import logging
import time

# Configurar logging a stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [DEBUG] - %(levelname)s - %(message)s')
logger = logging.getLogger("DebugSTT")

# Añadir raíz al path
sys.path.append(os.getcwd())

print("================================================================")
print("   DIAGNOSTICO DE STT (AUDIO TRANSCRIPTION) - COLEGA AI")
print("================================================================")

# 1. Comprobar importación de Vosk
print("\n[1] Verificando librería 'vosk'...")
try:
    import vosk
    print("[OK] Vosk importado correctamente.")
    print(f"   Ubicación: {os.path.dirname(vosk.__file__)}")
except ImportError as e:
    print(f"[ERROR] ERROR CRITICO: No se puede importar 'vosk'.")
    print(f"   Detalle: {e}")
    print("   Solución: Ejecutar 'pip install vosk' en el entorno virtual.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] ERROR DESCONOCIDO al importar vosk: {e}")
    sys.exit(1)

# 2. Comprobar directorio de modelos
print("\n[2] Verificando modelos de voz...")
MODEL_PATH = "vosk-models/es"
if os.path.exists(MODEL_PATH):
    print(f"[OK] Directorio de modelo encontrado: {MODEL_PATH}")
    files = os.listdir(MODEL_PATH)
    print(f"   Archivos encontrados ({len(files)}): {files[:5]}...")
    if not any(f in files for f in ['conf', 'am', 'graph', 'ivector']):
        print("[WARN]  ADVERTENCIA: La estructura del modelo parece sospechosa (faltan carpetas estandar de Kaldi).")
else:
    print(f"[ERROR] ERROR: No se encuentra el directorio '{MODEL_PATH}'.")
    print("   Solución: Ejecutar 'python resources/tools/download_vosk_model.py'")
    # No salimos aquí, tal vez la configuración apunte a otro lugar

# 3. Probar carga de modelos Vosk
print("\n[3] Probando carga del modelo Vosk (Aislamiento)...")
try:
    model = vosk.Model(MODEL_PATH)
    print("[OK] Modelo cargado exitosamente en memoria.")
except Exception as e:
    print(f"[ERROR] ERROR CRITICO: Falló la carga del modelo Vosk.")
    print(f"   Excepción: {e}")
    sys.exit(1)

# 4. Probar inicialización del Servicio STT
print("\n[4] Probando inicialización del Servicio STT...")
try:
    # Establecer configuración ficticia si es necesario, pero ConfigManager maneja el archivo faltante
    from modules.services.stt_service import STTService
    
    print("   -> Instanciando STTService...")
    # Esto intenta conectar al Bus, lo cual podría fallar si no está corriendo, 
    # pero no debería crashear el script si se maneja adecuadamente.
    service = STTService()
    
    if service.vosk_model:
        print("[OK] STTService inicializó el modelo Vosk internamente.")
    else:
        print("[ERROR] STTService NO pudo inicializar el modelo Vosk (vosk_model es None).")
        
    print("[OK] STTService instanciado sin crashear.")

except ImportError as e:
    print(f"[ERROR] ERROR DE IMPORTACIÓN: {e}")
    print("   Verifica que estás ejecutando desde la raíz del proyecto.")
except Exception as e:
    print(f"[ERROR] ERROR CRITICO al iniciar STTService: {e}")
    import traceback
    traceback.print_exc()

print("\n================================================================")
print("   DIAGNÓSTICO COMPLETADO")
print("================================================================")
