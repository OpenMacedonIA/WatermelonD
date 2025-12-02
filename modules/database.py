import sqlite3
import logging
import os
from datetime import datetime
from collections import deque

logger = logging.getLogger("NeoDatabase")

class DatabaseManager:
    def __init__(self, db_path="database/brain.db"):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def get_connection(self):
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                logger.error(f"Error connecting to database: {e}")
        return self.conn

    def init_db(self):
        """Initialize the database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table for storing raw interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT,
                neo_response TEXT,
                intent_name TEXT
            )
        ''')

        # Table for storing learned facts (Key-Value)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                key TEXT PRIMARY KEY,
                value TEXT,
                learned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for learned aliases (Trigger -> Command)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aliases (
                trigger TEXT PRIMARY KEY,
                command TEXT,
                learned_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for episodic memory (Events)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                details TEXT,
                sentiment TEXT,
                context_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for Cortex Concepts (Generalized Memory)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concepts (
                word TEXT PRIMARY KEY,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                frequency INTEGER DEFAULT 1,
                sentiment_score REAL DEFAULT 0.0
            )
        ''')

        # Table for Concept Associations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_word TEXT,
                interaction_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(concept_word) REFERENCES concepts(word)
            )
        ''')

        # Table for Knowledge Graph Relations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                target TEXT,
                relation_type TEXT,
                weight REAL DEFAULT 1.0,
                UNIQUE(source, target, relation_type)
            )
        ''')

        # Table for Proactive Surprises (to avoid repetition)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS surprises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for Daily Summaries (Long Term Memory)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                date DATE PRIMARY KEY,
                summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for File Indexing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                name TEXT,
                extension TEXT,
                size INTEGER,
                modified_at DATETIME,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        # FTS5 Virtual Tables for Fast Search
        try:
            # Facts FTS
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(key, value, content='facts', content_rowid='rowid')
            ''')
            # Triggers to keep facts_fts in sync
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
                  INSERT INTO facts_fts(rowid, key, value) VALUES (new.rowid, new.key, new.value);
                END;
            ''')
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
                  INSERT INTO facts_fts(facts_fts, rowid, key, value) VALUES('delete', old.rowid, old.key, old.value);
                END;
            ''')
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
                  INSERT INTO facts_fts(facts_fts, rowid, key, value) VALUES('delete', old.rowid, old.key, old.value);
                  INSERT INTO facts_fts(rowid, key, value) VALUES (new.rowid, new.key, new.value);
                END;
            ''')

            # Memory FTS
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(event_type, details, content='episodic_memory', content_rowid='id')
            ''')
            # Triggers for memory_fts
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON episodic_memory BEGIN
                  INSERT INTO memory_fts(rowid, event_type, details) VALUES (new.id, new.event_type, new.details);
                END;
            ''')
            
            logger.info("FTS5 tables and triggers initialized.")
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 not supported or error initializing: {e}. Falling back to standard search.")

        conn.commit()
        logger.info("Database initialized.")

    def log_interaction(self, user_input, neo_response, intent_name=None):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT INTO interactions (user_input, neo_response, intent_name) VALUES (?, ?, ?)",
                (user_input, neo_response, intent_name)
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error logging interaction: {e}")

    def get_recent_interactions(self, limit=50):
        conn = self.get_connection()
        cursor = conn.execute(
            "SELECT * FROM interactions ORDER BY timestamp DESC LIMIT ?", 
            (limit,)
        )
        return cursor.fetchall()

    def add_fact(self, key, value):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO facts (key, value, learned_at) VALUES (?, ?, ?)",
                (key.lower(), value, datetime.now())
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding fact: {e}")
            return False

    def get_fact(self, key):
        conn = self.get_connection()
        cursor = conn.execute("SELECT value FROM facts WHERE key = ?", (key.lower(),))
        row = cursor.fetchone()
        return row['value'] if row else None

    def search_facts(self, query):
        """Search for facts using FTS5 if available, else LIKE."""
        conn = self.get_connection()
        try:
            # Try FTS search
            # FTS query syntax: "query*" for prefix matching
            fts_query = f'"{query}" OR {query}*' 
            cursor = conn.execute(
                "SELECT key, value FROM facts_fts WHERE facts_fts MATCH ? ORDER BY rank LIMIT 10", 
                (fts_query,)
            )
            return cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback to LIKE
            wildcard = f"%{query.lower()}%"
            cursor = conn.execute(
                "SELECT key, value FROM facts WHERE key LIKE ? OR value LIKE ?", 
                (wildcard, wildcard)
            )
            return cursor.fetchall()

    def add_alias(self, trigger, command):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO aliases (trigger, command, learned_at) VALUES (?, ?, ?)",
                (trigger.lower(), command.lower(), datetime.now())
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding alias: {e}")
            return False

    def get_alias(self, trigger):
        conn = self.get_connection()
        cursor = conn.execute("SELECT command FROM aliases WHERE trigger = ?", (trigger.lower(),))
        row = cursor.fetchone()
        return row['command'] if row else None
    
    def get_all_aliases(self):
        conn = self.get_connection()
        cursor = conn.execute("SELECT trigger, command FROM aliases")
        return {row['trigger']: row['command'] for row in cursor.fetchall()}

    def log_event(self, event_type, details, sentiment="neutral", context_json="{}"):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT INTO episodic_memory (event_type, details, sentiment, context_json) VALUES (?, ?, ?, ?)",
                (event_type, details, sentiment, context_json)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging event: {e}")
            return False

    def get_recent_events(self, event_type, limit=1):
        conn = self.get_connection()
        cursor = conn.execute(
            "SELECT * FROM episodic_memory WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?", 
            (event_type, limit)
        )
        return cursor.fetchall()

    def search_memories(self, query, limit=5):
        """Search episodic memory using FTS5 if available, else LIKE."""
        conn = self.get_connection()
        try:
            fts_query = f'"{query}" OR {query}*'
            cursor = conn.execute(
                "SELECT event_type, details, timestamp FROM memory_fts WHERE memory_fts MATCH ? ORDER BY rank LIMIT ?", 
                (fts_query, limit)
            )
            # We need timestamp, but FTS table might not have it if we didn't include it. 
            # Actually we didn't include timestamp in FTS table definition above.
            # Let's join or just fetch from main table using rowid if needed, 
            # BUT for simplicity let's just use what we have or fix the FTS definition.
            # Wait, I defined FTS as external content table (content='episodic_memory').
            # So we can select other columns from the virtual table if the backing table has them? 
            # No, FTS5 external content tables only allow querying columns declared in FTS.
            # We need to join with the main table to get the timestamp.
            
            # Correctly join FTS table with main table to get timestamp
            cursor = conn.execute(
                '''
                SELECT e.event_type, e.details, e.timestamp 
                FROM episodic_memory e
                JOIN memory_fts f ON e.id = f.rowid
                WHERE memory_fts MATCH ? 
                ORDER BY f.rank 
                LIMIT ?
                ''',
                (fts_query, limit)
            )
            return cursor.fetchall()
        except sqlite3.OperationalError:
            wildcard = f"%{query.lower()}%"
            cursor = conn.execute(
                "SELECT event_type, details, timestamp FROM episodic_memory WHERE details LIKE ? OR event_type LIKE ? ORDER BY timestamp DESC LIMIT ?", 
                (wildcard, wildcard, limit)
            )
            return cursor.fetchall()

    # --- Cortex Methods ---
    def update_concept(self, word, sentiment_delta=0.0):
        conn = self.get_connection()
        try:
            # Check if exists
            cursor = conn.execute("SELECT frequency, sentiment_score FROM concepts WHERE word = ?", (word,))
            row = cursor.fetchone()
            
            if row:
                new_freq = row['frequency'] + 1
                new_sent = row['sentiment_score'] + sentiment_delta
                conn.execute(
                    "UPDATE concepts SET last_seen = ?, frequency = ?, sentiment_score = ? WHERE word = ?",
                    (datetime.now(), new_freq, new_sent, word)
                )
            else:
                conn.execute(
                    "INSERT INTO concepts (word, sentiment_score) VALUES (?, ?)",
                    (word, sentiment_delta)
                )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating concept '{word}': {e}")
            return False

    def get_concept(self, word):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM concepts WHERE word = ?", (word,))
        return cursor.fetchone()

    def get_top_concepts(self, limit=5):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM concepts ORDER BY frequency DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def add_relation(self, source, target, relation_type, weight=1.0):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO relations (source, target, relation_type, weight) VALUES (?, ?, ?, ?)",
                (source.lower(), target.lower(), relation_type.lower(), weight)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding relation {source}->{target}: {e}")
            return False

    def get_related_concepts(self, source, relation_type=None):
        conn = self.get_connection()
        if relation_type:
            cursor = conn.execute(
                "SELECT target, relation_type, weight FROM relations WHERE source = ? AND relation_type = ?", 
                (source.lower(), relation_type.lower())
            )
        else:
            cursor = conn.execute(
                "SELECT target, relation_type, weight FROM relations WHERE source = ?", 
                (source.lower(),)
            )
        return cursor.fetchall()

        return cursor.fetchall()

    def get_path(self, start_node, end_node, max_depth=3):
        """
        Finds a path between two concepts using BFS (Breadth-First Search).
        Returns a list of (node, relation, next_node) tuples.
        """
        start_node = start_node.lower()
        end_node = end_node.lower()
        
        queue = deque([(start_node, [])]) # (current_node, path_so_far)
        visited = set([start_node])
        
        while queue:
            current, path = queue.popleft()
            
            if current == end_node:
                return path
            
            if len(path) >= max_depth:
                continue
            
            # Get neighbors
            relations = self.get_related_concepts(current)
            for target, rel_type, _ in relations:
                if target not in visited:
                    visited.add(target)
                    new_path = path + [(current, rel_type, target)]
                    queue.append((target, new_path))
                    
        return None

    def infer_problems(self, source_node):
        """
        Infers potential problems by checking 'uses' or 'needs' relations.
        If A uses B, and B is 'down' or 'broken' (conceptually), then A might be affected.
        For this simple version, we just return dependencies that should be checked.
        """
        dependencies = []
        # Find everything source_node 'uses' or 'needs' or 'check'
        relations = self.get_related_concepts(source_node)
        for target, rel_type, _ in relations:
            if rel_type in ["uses", "needs", "check"]:
                dependencies.append(target)
                
        # Recursive check (depth 1)
        indirect = []
        for dep in dependencies:
            sub_rels = self.get_related_concepts(dep)
            for sub_target, sub_rel, _ in sub_rels:
                if sub_rel in ["uses", "needs", "check"]:
                    indirect.append(sub_target)
                    
        return list(set(dependencies + indirect))

    def log_surprise(self, topic, message):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT INTO surprises (topic, message) VALUES (?, ?)",
                (topic, message)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging surprise: {e}")
            return False

    def get_recent_surprises(self, topic, limit=1):
        conn = self.get_connection()
        cursor = conn.execute(
            "SELECT * FROM surprises WHERE topic = ? ORDER BY timestamp DESC LIMIT ?", 
            (topic, limit)
        )
        return cursor.fetchall()

    def get_interactions_by_date(self, date_str):
        """Get all interactions for a specific date (YYYY-MM-DD)."""
        conn = self.get_connection()
        # SQLite date function extracts YYYY-MM-DD from timestamp
        cursor = conn.execute(
            "SELECT user_input, neo_response FROM interactions WHERE date(timestamp) = ?", 
            (date_str,)
        )
        return cursor.fetchall()

    def add_daily_summary(self, date_str, summary):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO daily_summaries (date, summary) VALUES (?, ?)",
                (date_str, summary)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding daily summary: {e}")
            return False

    def get_daily_summary(self, date_str):
        conn = self.get_connection()
        cursor = conn.execute("SELECT summary FROM daily_summaries WHERE date = ?", (date_str,))
        row = cursor.fetchone()
        return row['summary'] if row else None

    def close(self):
        if self.conn:
            self.conn.close()

    # --- File Indexing Methods ---

    def index_file(self, path, name, extension, size, mtime):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO files_index (path, name, extension, size, modified_at, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (path, name, extension, size, mtime, datetime.now())
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error indexing file {path}: {e}")
            return False

    def search_files_index(self, query, limit=10):
        """Search files by name using LIKE."""
        conn = self.get_connection()
        wildcard = f"%{query.lower()}%"
        cursor = conn.execute(
            "SELECT path, name, size FROM files_index WHERE name LIKE ? LIMIT ?",
            (wildcard, limit)
        )
        return cursor.fetchall()

    def clear_file_index(self):
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM files_index")
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error clearing file index: {e}")
            return False
