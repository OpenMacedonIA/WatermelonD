import json
import os
import pickle
import sqlite3
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NeoTrainer")

DATA_DIR = "training_data"
MODEL_DIR = "brain"
MODEL_FILE = os.path.join(MODEL_DIR, "chat_model.pkl")
DB_FILE = os.path.join(MODEL_DIR, "chat.db")

def init_db():
    """Inicializa la base de datos de respuestas."""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS responses
                 (id INTEGER PRIMARY KEY, text TEXT)''')
    c.execute('DELETE FROM responses') # Limpiar tabla antes de reentrenar
    conn.commit()
    return conn

def load_data():
    """Carga todos los JSONs del directorio de datos."""
    if not os.path.exists(DATA_DIR):
        logger.warning(f"Directorio '{DATA_DIR}' no encontrado. Creándolo...")
        os.makedirs(DATA_DIR)
        return []

    conversations = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(DATA_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Verificar si es una lista de conversaciones (lista de listas)
                        if data and isinstance(data[0], list):
                            conversations.extend(data)
                        else:
                            # Es una única conversación (lista de mensajes)
                            conversations.append(data)
                    else:
                        logger.warning(f"Formato incorrecto en {filename}. Se esperaba una lista.")
            except Exception as e:
                logger.error(f"Error leyendo {filename}: {e}")
    
    return conversations

def train():
    logger.info("Iniciando entrenamiento AVANZADO de Neo Chat (v2)...")
    
    raw_conversations = load_data()
    if not raw_conversations:
        logger.warning("No hay datos de entrenamiento. Añade archivos JSON en 'training_data/'.")
        return

    training_inputs = []
    training_responses = []
    
    # Procesar Conversaciones con Ventana de Contexto
    # Input = [Contexto Previo] + [Separador] + [Mensaje Actual]
    # Target = [Mensaje Siguiente]
    
    SEPARATOR = " ||| "
    
    for conv in raw_conversations:
        # Asumimos que 'conv' es una lista de mensajes en orden cronológico
        for i in range(len(conv) - 1):
            current_msg = conv[i].get('text', '').strip()
            next_msg = conv[i+1].get('text', '').strip()
            
            prev_msg = ""
            if i > 0:
                prev_msg = conv[i-1].get('text', '').strip()
            
            if current_msg and next_msg:
                # Construimos el input con contexto
                # Si es el primer mensaje, el contexto es vacío
                if prev_msg:
                    combined_input = f"{prev_msg}{SEPARATOR}{current_msg}"
                else:
                    combined_input = current_msg
                
                training_inputs.append(combined_input)
                training_responses.append(next_msg)

    logger.info(f"Procesados {len(training_inputs)} pares de entrenamiento con contexto.")

    if not training_inputs:
        logger.warning("No se generaron datos válidos.")
        return

    # Entrenar TF-IDF con N-Grams de Caracteres
    # analyzer='char_wb': Crea n-grams solo dentro de los límites de las palabras (mejor para typos)
    # ngram_range=(3, 5): Mira grupos de 3, 4 y 5 letras.
    logger.info("Entrenando vectorizador (Char N-Grams 3-5)...")
    vectorizer = TfidfVectorizer(
        analyzer='char_wb', 
        ngram_range=(3, 5), 
        min_df=1, # Incluir todo, aunque sea raro (importante para datos pequeños)
        lowercase=True
    )
    tfidf_matrix = vectorizer.fit_transform(training_inputs)

    # Guardar en Base de Datos
    conn = init_db()
    c = conn.cursor()
    for idx, resp in enumerate(training_responses):
        c.execute("INSERT INTO responses (id, text) VALUES (?, ?)", (idx, resp))
    conn.commit()
    conn.close()

    # Guardar Modelo
    model_data = {
        'vectorizer': vectorizer,
        'tfidf_matrix': tfidf_matrix,
        'separator': SEPARATOR # Guardamos el separador para usarlo en runtime
    }
    
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model_data, f)
        
    logger.info(f"Modelo v2 guardado exitosamente en '{MODEL_FILE}'.")
    logger.info("¡Entrenamiento completado!")

if __name__ == "__main__":
    train()
