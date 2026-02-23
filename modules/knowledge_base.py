import os
import logging
import glob
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import pypdf

# Configurar logger
logger = logging.getLogger("KnowledgeBase")

# Suprimir advertencias de HuggingFace Transformers (position_ids UNEXPECTED)
import transformers
transformers.logging.set_verbosity_error()

class KnowledgeBase:
    def __init__(self, docs_path: str = "docs", db_path: str = "database/knowledge_db"):
        self.docs_path = docs_path
        self.db_path = db_path
        self.collection_name = "colega_docs"
        
        # Inicializar Cliente ChromaDB
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Inicializar Función de Incrustación (usando un modelo pequeño y eficiente)
        # all-MiniLM-L6-v2 es un buen equilibrio entre velocidad y rendimiento
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        # Obtener o Crear Colección
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn
        )
        
        logger.info(f"KnowledgeBase initialized at {self.db_path}")

    def ingest_docs(self, force: bool = False):
        """
        Escanea el directorio de documentos e ingesta archivos markdown en la base de datos vectorial.
        Si force es True, limpia la colección primero.
        """
        if force:
            logger.info("Forzando re-ingesta. Limpiando colección...")
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn
            )

        # Encontrar todos los archivos soportados
        extensions = ['*.md', '*.txt', '*.pdf']
        docs_files = []
        for ext in extensions:
            docs_files.extend(glob.glob(os.path.join(self.docs_path, "**", ext), recursive=True))
        
        if not docs_files:
            logger.warning(f"No supported documents found in {self.docs_path}")
            return

        logger.info(f"Found {len(docs_files)} documents to ingest.")
        
        count = 0
        for file_path in docs_files:
            try:
                content = ""
                if file_path.endswith('.pdf'):
                    reader = pypdf.PdfReader(file_path)
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                # La división simple por párrafos o encabezados podría ser mejor, 
                # pero por ahora hagamos una ventana deslizante o división por párrafos.
                # Dividamos por retornos de carro dobles para obtener párrafos.
                chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
                
                if not chunks:
                    continue

                # Preparar datos para Chroma
                ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
                metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]
                
                # Añadir a la colección
                self.collection.upsert(
                    documents=chunks,
                    ids=ids,
                    metadatas=metadatas
                )
                count += len(chunks)
                logger.debug(f"Ingested {len(chunks)} chunks from {file_path}")
                
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {e}")

        logger.info(f"Ingestion complete. Total chunks: {count}")

    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        """
        Consulta la base de conocimientos buscando contexto relevante.
        Devuelve una lista de fragmentos de texto (chunks).
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # results['documents'] es una lista de listas (una lista por consulta)
            if results['documents'] and results['documents'][0]:
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return []

if __name__ == "__main__":
    # Prueba de ejecución
    logging.basicConfig(level=logging.INFO)
    kb = KnowledgeBase(docs_path="/home/jrodriiguezg/backup/codigos/COLEGA/docs")
    kb.ingest_docs()
    results = kb.query("¿Qué es la arquitectura cognitiva?")
    print("Query Results:")
    for res in results:
        print(f"- {res[:100]}...")
