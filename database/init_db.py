from modules.database import DatabaseManager
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO)

def init():
    print("Inicializando Base de Datos Neo Brain...")
    try:
        db = DatabaseManager()
        # El método __init__ de DatabaseManager llama a init_db(), que crea las tablas si no existen.
        # También podemos comprobar la conexión aquí explícitamente.
        conn = db.get_connection()
        print("Base de datos 'brain.db' creada/verificada exitosamente.")
        db.close()
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")
        exit(1)

if __name__ == "__main__":
    init()
