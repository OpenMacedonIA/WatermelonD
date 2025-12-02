import logging
import os

# Crear directorio de logs si no existe
os.makedirs('logs', exist_ok=True)

def setup_logger(name, log_file, level=logging.INFO):
    """Función para configurar un logger específico."""
    handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

# Configurar loggers globales
app_logger = setup_logger('app', 'logs/app.log')
tts_logger = setup_logger('tts', 'logs/tts.log')
vosk_logger = setup_logger('vosk', 'logs/vosk.log')
video_logger = setup_logger('video', 'logs/video.log')
