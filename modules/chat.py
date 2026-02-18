import logging
from modules.logger import app_logger
from modules.knowledge_base import KnowledgeBase
from modules.sentiment import SentimentManager

class ChatManager:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.context_history = []
        self.brain = None # Injected later
        self.knowledge_base = KnowledgeBase() # Initialize RAG
        self.sentiment_manager = SentimentManager()
        
        # System Prompt Base
        self.base_system_prompt = (
            "Eres TIO (Tecnología de Inteligencia Organizada), un asistente sarcástico pero útil. "
            "Responde de forma breve y directa. "
            "Si no sabes algo, admítelo. "
            "Usa jerga española coloquial (tío, colega, flipas) pero mantén la precisión técnica."
        )

    def reset_context(self):
        """Limpia el historial de conversación."""
        self.context_history = []

    def get_response(self, user_input, system_context=None):
        """Genera una respuesta completa (bloqueante)."""
        prompt = self._build_prompt(user_input, system_context)
        return self.ai_engine.generate_response(prompt)

    def get_response_stream(self, user_input, system_context=None):
        """Genera una respuesta en streaming."""
        prompt = self._build_prompt(user_input, system_context)
        return self.ai_engine.generate_response_stream(prompt)

    def _build_prompt(self, user_input, system_context=None):
        """Construye el prompt con historial, contexto RAG y personalidad para Gemma 2."""
        
        # 0. Sentiment Analysis
        sentiment, _ = self.sentiment_manager.analyze(user_input)
        current_system_prompt = self.base_system_prompt
        
        if sentiment == 'angry':
            current_system_prompt += " EL USUARIO ESTÁ ENFADADO. No te disculpes. Ponte chulo."
        elif sentiment == 'positive':
            current_system_prompt += " EL USUARIO ESTÁ CONTENTO. Sé entusiasta."
        
        # 1. Retrieve RAG Context
        rag_context = ""
        try:
            docs = self.knowledge_base.query(user_input)
            if docs:
                rag_context = "\nCONTEXTO TÉCNICO (Documentación):\n" + "\n---\n".join(docs) + "\n"
        except Exception as e:
            app_logger.error(f"Error retrieving RAG context: {e}")

        # 2. Build Full Prompt using Gemma 2 Template
        # Format: <start_of_turn>user\n{content}<end_of_turn>\n<start_of_turn>model\n
        
        full_prompt = ""

        # History (Last 5 turns)
        for turn in self.context_history[-5:]:
            full_prompt += f"<start_of_turn>user\n{turn['user']}<end_of_turn>\n"
            full_prompt += f"<start_of_turn>model\n{turn['assistant']}<end_of_turn>\n"

        # Current Context & Input
        # We inject system prompt into the start of the final user turn or logically preceding it.
        # For Gemma, it's often best to put system instructions in the first user turn, 
        # but since we rotate history, we will prepend it to the current user input for immediate context.
        
        final_user_content = f"{current_system_prompt}\n\n"
        
        if rag_context:
            final_user_content += f"{rag_context}\n"
            
        if system_context:
            final_user_content += f"CONTEXTO DEL SISTEMA: {system_context}\n"
            
        final_user_content += f"PREGUNTA DEL USUARIO: {user_input}"
        
        full_prompt += f"<start_of_turn>user\n{final_user_content}<end_of_turn>\n<start_of_turn>model\n"
        
        return full_prompt

    def update_history(self, user, assistant):
        """Actualiza el historial."""
        self.context_history.append({'user': user, 'assistant': assistant})
