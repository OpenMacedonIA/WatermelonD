import json
import os
import re
import logging
from ctypes import *
from contextlib import contextmanager

logger = logging.getLogger("Neo")

def load_json_data(filepath, key=None, default=None):
    """Carga datos de un fichero JSON de forma segura."""
    if default is None:
        default = []
        
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if key:
                    return data.get(key, default)
                return data
        else:
            logger.warning(f"Fichero {filepath} no encontrado.")
            return default
    except Exception as e:
        logger.error(f"Error cargando {filepath}: {e}")
        return default

def normalize_text(text):
    """
    Normaliza texto para Vosk.
    IMPORTANTE: El modelo en español ESPERA acentos.
    Solo pasamos a minúsculas y quitamos puntuación extraña, pero mantenemos tildes y ñ.
    """
    if not text: return ""
    # Convertir a minúsculas
    text = text.lower()
    # Eliminar puntuación excepto tildes y ñ (que son letras)
    # Mantenemos letras, números y espacios.
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def number_to_text(text):
    """Convierte números simples a texto (básico para gramática)."""
    nums = {
        "100": "cien", "40": "cuarenta", "1": "uno", "2": "dos", "3": "tres",
        "4": "cuatro", "5": "cinco", "10": "diez", "20": "veinte", "30": "treinta"
    }
    words = text.split()
    new_words = []
    for w in words:
        if w in nums:
            new_words.append(nums[w])
        elif w.isdigit():
            new_words.append(w) 
        else:
            new_words.append(w)
    return " ".join(new_words)

# --- Supresión de Errores ALSA ---
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_error():
    try:
        asound = cdll.LoadLibrary('libasound.so')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield
