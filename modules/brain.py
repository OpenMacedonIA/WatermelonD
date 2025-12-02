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
    Brain handles Episodic Memory and Learning.
    Block 2 Upgrade: Context Snapshots & Fuzzy Recall.
    """
    def __init__(self):
        self.db = DatabaseManager()
        self.short_term_memory = deque(maxlen=5) # Context of last 5 interactions
        self.aliases_cache = self.db.get_all_aliases()
        self.ai_engine = None # Injected later
        logger.info("Neo Brain (Block 2 Upgraded) initialized.")

    def set_ai_engine(self, ai_engine):
        self.ai_engine = ai_engine

    def process_input(self, user_input):
        """
        Check if the input matches a learned alias.
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

    # --- Block 2: Advanced Episodic Memory ---

    def remember_event(self, event_type, details, sentiment="neutral"):
        """
        Store an episodic event with a snapshot of the current context.
        """
        # Capture Context (Mocked for now, could be real system stats)
        context = {
            "last_interaction": self.get_last_context(),
            "system_load": "low", # Placeholder
            "active_window": "unknown" # Placeholder
        }
        context_json = json.dumps(context)
        
        success = self.db.log_event(event_type, details, sentiment, context_json)
        if success:
            logger.info(f"Brain: Remembered event '{event_type}' -> '{details}'")
        return success

    def recall_events(self, event_type, limit=5, fuzzy_query=None):
        """
        Recall recent episodic events.
        If fuzzy_query is provided, filters events by similarity to details.
        """
        events = self.db.get_recent_events(event_type, limit=limit)
        
        if not fuzzy_query or not fuzz:
            return events
            
        # Fuzzy Filter
        filtered_events = []
        for event in events:
            # event is a Row object, access by name
            details = event['details']
            score = fuzz.token_set_ratio(fuzzy_query, details)
            if score > 60: # Threshold
                filtered_events.append(event)
                logger.debug(f"Brain: Fuzzy match '{fuzzy_query}' vs '{details}' = {score}")
        
        return filtered_events

    # --- RAG: Retrieval Augmented Generation ---

    def retrieve_context(self, user_input):
        """
        Retrieves relevant context from Facts and Episodic Memory based on user input.
        Returns a formatted string or None.
        """
        if not user_input:
            return None

        # 1. Extract potential keywords (simplified)
        # We use the whole input for LIKE search, which is crude but effective for "Who is X?"
        # For better results, we might want to extract nouns, but let's start simple.
        
        # Avoid searching for common stopwords if possible, but for now pass the raw input
        # or maybe just the longest word? No, let's pass the whole phrase for now 
        # but if it's too long, maybe just search for entities.
        # Let's try searching for the input directly first.
        
        # Optimization: If input is "Who is X", search for "X"
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
        Generates a summary of yesterday's interactions and stores it.
        Should be called once a day (e.g. at startup or midnight).
        """
        from datetime import datetime, timedelta
        
        # Calculate yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Check if summary already exists
        if self.db.get_daily_summary(yesterday):
            logger.info(f"Summary for {yesterday} already exists.")
            return False

        # Get interactions
        interactions = self.db.get_interactions_by_date(yesterday)
        if not interactions:
            logger.info(f"No interactions found for {yesterday}.")
            return False

        if not self.ai_engine:
            logger.warning("Cannot consolidate memory: AI Engine not available.")
            return False

        # Format for summarization
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
