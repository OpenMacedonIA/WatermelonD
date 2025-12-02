import os
import pickle
import sqlite3
import logging
import logging
from sklearn.metrics.pairwise import cosine_similarity
from modules.sentiment import SentimentManager

logger = logging.getLogger("NeoChat")

MODEL_DIR = "brain"
MODEL_FILE = os.path.join(MODEL_DIR, "chat_model.pkl")
DB_FILE = os.path.join(MODEL_DIR, "chat.db")

class ChatManager:
    def __init__(self, ai_engine=None):
        self.ai_engine = ai_engine
        self.is_ready = False
        if self.ai_engine:
            self.is_ready = self.ai_engine.is_ready
        
        # Personalidad base de TIO
        self.system_prompt = (
            "Eres TIO, un asistente sarcástico, divertido y muy colega. "
            "Tu objetivo es entretener y ayudar, pero siempre con un toque de humor. "
            "Responde SIEMPRE en CASTELLANO DE ESPAÑA (Jerga de calle). "
            "Usa expresiones como: 'Tío', 'Tronco', 'Fiera', 'Máquina', 'Jefe', 'Bro'. "
            "NO seas robótico. Si no sabes algo, invéntate una excusa graciosa o dilo con estilo. "
            "NO USES EMOJIS. "
            "SÉ BREVE y DIRECTO (Max 40 palabras), salvo que cuentes una historia. "
            "IMPORTANTE: Te ejecutas en un servidor Linux como un servicio de usuario llamado 'neo.service'. "
            "Si te mencionan 'systemctl --user restart neo.service', es el comando para reiniciarte. "
            "Si te piden reiniciarte, confirma que ese es el comando correcto."
        )

        self.history = []
        self.sentiment_manager = SentimentManager()

    def get_response(self, user_input, system_context=None):
        """Genera una respuesta usando Gemma 2B, con contexto RAG, Sentimiento y Sistema."""
        if not self.ai_engine or not self.ai_engine.is_ready:
            return "Lo siento, mi cerebro está apagado."

        try:
            # 0. Análisis de Sentimiento
            sentiment, score = self.sentiment_manager.analyze(user_input)
            
            # Ajuste de personalidad según sentimiento
            current_prompt = self.system_prompt
            if sentiment == 'angry':
                current_prompt += " EL USUARIO ESTÁ ENFADADO. No te disculpes. Ponte chulo. Dile que no pague sus frustraciones contigo. Sé cortante y sarcástico."
            elif sentiment == 'positive':
                current_prompt += " EL USUARIO ESTÁ CONTENTO. Sé entusiasta, celebra con él y usa exclamaciones."
            elif sentiment == 'negative':
                current_prompt += " EL USUARIO ESTÁ TRISTE O MOLESTO. Sé empático y suave."

            # 1. Recuperar contexto del Brain (RAG)
            rag_context = ""
            if hasattr(self, 'brain') and self.brain:
                 found_context = self.brain.retrieve_context(user_input)
                 if found_context:
                     rag_context = f"\n[INFORMACIÓN RECUPERADA DE TU MEMORIA]:\n{found_context}\n"

            # 1.1. Inyectar Estado del Sistema (Contexto Situacional)
            import psutil
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent
            sys_context = f"\n[ESTADO DEL SERVIDOR]: CPU {cpu_usage}%, RAM {ram_usage}%. Si te preguntan, úsalo."

            # 2. Construir el prompt manualmente (Gemma Format)
            # <start_of_turn>user\n{content}<end_of_turn>\n<start_of_turn>model\n{response}<end_of_turn>
            
            full_prompt = ""
            
            # Instrucción del sistema + Contexto RAG + Contexto de Acción (Ping, etc) + Estado Sistema
            system_instruction = current_prompt + rag_context + sys_context
            
            if system_context:
                system_instruction += f"\n[RESULTADO DE ACCIÓN DEL SISTEMA]: {system_context}\nUsa esta información para responder al usuario."
            
            if self.history:
                # Historial
                first_turn = True
                for turn in self.history:
                    user_msg = turn['user']
                    if first_turn:
                        # Inyectar sistema en el primer turno
                        user_msg = f"{system_instruction}\n\n{user_msg}"
                        first_turn = False
                    
                    full_prompt += f"<start_of_turn>user\n{user_msg}<end_of_turn>\n"
                    full_prompt += f"<start_of_turn>model\n{turn['bot']}<end_of_turn>\n"
                
                # Turno actual
                full_prompt += f"<start_of_turn>user\n{user_input}<end_of_turn>\n<start_of_turn>model\n"
            else:
                # Sin historial: Sistema + Input actual
                full_prompt = f"<start_of_turn>user\n{system_instruction}\n\n{user_input}<end_of_turn>\n<start_of_turn>model\n"
            
            # 3. Generar respuesta
            response = self.ai_engine.generate_response(full_prompt)
            
            # 3.1. Limpieza de Emojis (Regex)
            # Elimina caracteres en rangos Unicode de emojis
            import re
            response = re.sub(r'[^\w\s,.\-!¡?¿:;]', '', response).strip()
            
            # 4. Guardar en historial
            self.history.append({'user': user_input, 'bot': response})
            if len(self.history) > 20:
                self.history.pop(0)
                
            return response

        except Exception as e:
            logger.error(f"Error generando respuesta de chat: {e}")
            return "Me ha dado un pantallazo azul mental, tío."

    def get_response_stream(self, user_input, system_context=None):
        """Genera respuesta en streaming y gestiona historial."""
        if not self.ai_engine or not self.ai_engine.is_ready:
            yield "Lo siento, mi cerebro está apagado."
            return

        try:
            # 0. Análisis de Sentimiento (Igual que get_response)
            sentiment, score = self.sentiment_manager.analyze(user_input)
            
            current_prompt = self.system_prompt
            if sentiment == 'angry':
                current_prompt += " EL USUARIO ESTÁ ENFADADO. No te disculpes. Ponte chulo. Dile que no pague sus frustraciones contigo. Sé cortante y sarcástico."
            elif sentiment == 'positive':
                current_prompt += " EL USUARIO ESTÁ CONTENTO. Sé entusiasta, celebra con él y usa exclamaciones."
            elif sentiment == 'negative':
                current_prompt += " EL USUARIO ESTÁ TRISTE O MOLESTO. Sé empático y suave."

            # 1. Recuperar contexto del Brain (RAG)
            rag_context = ""
            if hasattr(self, 'brain') and self.brain:
                 found_context = self.brain.retrieve_context(user_input)
                 if found_context:
                     rag_context = f"\n[INFORMACIÓN RECUPERADA DE TU MEMORIA]:\n{found_context}\n"

            # 1.1. Inyectar Estado del Sistema
            import psutil
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent
            sys_context = f"\n[ESTADO DEL SERVIDOR]: CPU {cpu_usage}%, RAM {ram_usage}%. Si te preguntan, úsalo."

            # 2. Construir el prompt
            full_prompt = ""
            system_instruction = current_prompt + rag_context + sys_context
            
            if system_context:
                system_instruction += f"\n\n[RESULTADO DE LA ACCIÓN DEL SISTEMA (CRÍTICO)]: {system_context}\n" \
                                      f"INSTRUCCIÓN: El usuario ya ha ejecutado esta acción. NO preguntes qué hacer. " \
                                      f"Simplemente explica el resultado al usuario con tu personalidad. " \
                                      f"Si el resultado es un error, dilo. Si es éxito, confírmalo."
            
            if self.history:
                first_turn = True
                for turn in self.history:
                    user_msg = turn['user']
                    if first_turn:
                        user_msg = f"{system_instruction}\n\n{user_msg}"
                        first_turn = False
                    full_prompt += f"<start_of_turn>user\n{user_msg}<end_of_turn>\n"
                    full_prompt += f"<start_of_turn>model\n{turn['bot']}<end_of_turn>\n"
                full_prompt += f"<start_of_turn>user\n{user_input}<end_of_turn>\n<start_of_turn>model\n"
            else:
                full_prompt = f"<start_of_turn>user\n{system_instruction}\n\n{user_input}<end_of_turn>\n<start_of_turn>model\n"
            
            # 3. Generar Stream
            full_response = ""
            import re
            
            for chunk in self.ai_engine.generate_response_stream(full_prompt):
                # Filtrado básico de emojis en el chunk (puede romper emojis multibyte, pero es simple)
                chunk_clean = re.sub(r'[^\w\s,.\-!¡?¿:;]', '', chunk)
                full_response += chunk_clean
                yield chunk_clean
            
            # 4. Guardar en historial al finalizar
            self.history.append({'user': user_input, 'bot': full_response.strip()})
            if len(self.history) > 20:
                self.history.pop(0)

        except Exception as e:
            logger.error(f"Error generando stream de chat: {e}")
            yield " Error."

    def reset_context(self):
        """Olvida la historia reciente."""
        self.history = []

