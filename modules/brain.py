import logging
import json
from collections import deque
from modules.database import DatabaseManager
try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

logger = logging.getLogger("NeoBrain")

class Brain:
    """
    Brain maneja la Memoria Episódica y el Aprendizaje.
    Mejora del Bloque 2: Instantáneas de Contexto y Recuperación Difusa (Fuzzy Recall).
    """
    def __init__(self):
        self.db = DatabaseManager()
        self.short_term_memory = deque(maxlen=5) # Contexto de las últimas 5 interacciones
        self.aliases_cache = self.db.get_all_aliases()
        self.ai_engine = None # Inyectado más tarde
        logger.info("Neo Brain (Block 2 Upgraded) initialized.")

    def set_ai_engine(self, ai_engine):
        self.ai_engine = ai_engine

    def process_input(self, user_input):
        """
        Comprueba si la entrada coincide con un alias aprendido.
        """
        user_input_lower = user_input.lower()
        if user_input_lower in self.aliases_cache:
            return self.aliases_cache[user_input_lower]
        return None

    def learn_alias(self, trigger, command):
        success = self.db.add_alias(trigger, command)
        if success:
            self.aliases_cache[trigger.lower()] = command.lower()
        return success

    def store_interaction(self, user_input, neo_response, intent_name=None):
        self.short_term_memory.append({
            'user': user_input,
            'neo': neo_response,
            'intent': intent_name
        })
        self.db.log_interaction(user_input, neo_response, intent_name)

    def get_last_context(self):
        if self.short_term_memory:
            return self.short_term_memory[-1]
        return None

    # --- Bloque 2: Memoria Episódica Avanzada ---

    def remember_event(self, event_type, details, sentiment="neutral"):
        """
        Almacena un evento episódico con una instantánea del contexto actual.
        """
        # Capturar Contexto (Simulado por ahora, podrían ser estadísticas reales del sistema)
        context = {
            "last_interaction": self.get_last_context(),
            "system_load": "low", # Marcador de posición
            "active_window": "unknown" # Marcador de posición
        }
        context_json = json.dumps(context)
        
        success = self.db.log_event(event_type, details, sentiment, context_json)
        if success:
            logger.info(f"Brain: Remembered event '{event_type}' -> '{details}'")
        return success

    def recall_events(self, event_type, limit=5, fuzzy_query=None):
        """
        Recuperar eventos episódicos recientes.
        Si se proporciona fuzzy_query, filtra los eventos por similitud con los detalles.
        """
        events = self.db.get_recent_events(event_type, limit=limit)
        
        if not fuzzy_query or not fuzz:
            return events
            
        # Filtro Difuso (Fuzzy)
        filtered_events = []
        for event in events:
            # event es un objeto Row, acceder por nombre
            details = event['details']
            score = fuzz.token_set_ratio(fuzzy_query, details)
            if score > 60: # Umbral
                filtered_events.append(event)
                logger.debug(f"Brain: Fuzzy match '{fuzzy_query}' vs '{details}' = {score}")
        
        return filtered_events

    # --- RAG: Retrieval Augmented Generation (Generación Aumentada con Recuperación) ---

    def retrieve_context(self, user_input):
        """
        Recupera el contexto relevante de los Hechos y la Memoria Episódica basándose en la entrada del usuario.
        Devuelve una cadena formateada o None.
        """
        if not user_input:
            return None

        # 1. Extraer posibles palabras clave (simplificado)
        # Usamos toda la entrada para la búsqueda LIKE, que es rudo pero efectivo para "¿Quién es X?"
        # Para mejores resultados, podríamos querer extraer sustantivos, pero empecemos simple.
        
        # Evitar buscar palabras vacías comunes (stopwords) si es posible, pero por ahora pasamos la entrada cruda
        # ¿o tal vez solo la palabra más larga? No, pasemos la frase entera por ahora 
        # pero si es demasiado larga, quizás solo busquemos entidades.
        # Intentemos buscar la entrada directamente primero.
        
        # Optimización: Si la entrada es "Quién es X", buscar "X"
        search_term = user_input
        
        facts = self.db.search_facts(search_term)
        memories = self.db.search_memories(search_term, limit=3)
        
        context_parts = []
        
        if facts:
            context_parts.append("Hechos conocidos:")
            for fact in facts:
                context_parts.append(f"- {fact['key']}: {fact['value']}")
                
        if memories:
            context_parts.append("Recuerdos recientes:")
            for mem in memories:
                context_parts.append(f"- [{mem['timestamp']}] {mem['event_type']}: {mem['details']}")
                
        if not context_parts:
            return None
            
        return "\n".join(context_parts)

    def consolidate_memory(self):
        """
        Genera un resumen de las interacciones de ayer y lo almacena.
        Debería llamarse una vez al día (ej. en el arranque o a medianoche).
        """
        from datetime import datetime, timedelta
        
        # Calcular fecha de ayer
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Comprobar si ya existe el resumen
        if self.db.get_daily_summary(yesterday):
            logger.info(f"Summary for {yesterday} already exists.")
            return False

        # Obtener interacciones
        interactions = self.db.get_interactions_by_date(yesterday)
        if not interactions:
            logger.info(f"No interactions found for {yesterday}.")
            return False

        if not self.ai_engine:
            logger.warning("Cannot consolidate memory: AI Engine not available.")
            return False

        # Formatear para resumir
        text_block = "\n".join([f"User: {i['user_input']}\nNeo: {i['neo_response']}" for i in interactions])
        
        # Prompt
        prompt = (
            f"Resume brevemente las siguientes interacciones del día {yesterday}. "
            "Destaca los temas principales, comandos ejecutados y datos aprendidos. "
            "Usa un tono narrativo en tercera persona (ej: 'El usuario pidió...').\n\n"
            f"{text_block}\n\nResumen:"
        )

        try:
            summary = self.ai_engine.generate_response(prompt)
            if summary:
                self.db.add_daily_summary(yesterday, summary)
                logger.info(f"Memory consolidated for {yesterday}.")
                return True
        except Exception as e:
            logger.error(f"Error consolidating memory: {e}")
            
        return False
