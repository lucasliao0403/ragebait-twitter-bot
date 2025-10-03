import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.db_path = os.path.join(data_dir, "memory.db")
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                author TEXT,
                content TEXT,
                url TEXT,
                metadata TEXT
            )
        ''')

        # Create indexes for fast queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_author ON interactions(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(type)')

        conn.commit()
        conn.close()

    def log_interaction(self, interaction_data: Dict[str, Any]):
        """Log an interaction to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build metadata from extra fields
            metadata = {}
            if 'search_query' in interaction_data:
                metadata['search_query'] = interaction_data['search_query']
            if 'tweet_url' in interaction_data:
                metadata['target_url'] = interaction_data['tweet_url']

            metadata_json = json.dumps(metadata) if metadata else None

            # Insert interaction with parameterized query to prevent SQL injection
            cursor.execute('''
                INSERT INTO interactions (timestamp, type, content, author, url, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                interaction_data.get('type'),
                interaction_data.get('text'),  # 'text' field maps to 'content' column
                interaction_data.get('author'),
                interaction_data.get('url'),
                metadata_json
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error logging interaction to database: {e}")
            # Don't raise - we don't want to break the bot if logging fails

    def get_recent_interactions(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent interactions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM interactions
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (count,))

            rows = cursor.fetchall()
            conn.close()

            # Convert to list of dicts and parse metadata JSON
            interactions = []
            for row in rows:
                interaction = dict(row)
                if interaction.get('metadata'):
                    try:
                        interaction['metadata'] = json.loads(interaction['metadata'])
                    except json.JSONDecodeError:
                        interaction['metadata'] = {}
                interactions.append(interaction)

            return interactions

        except Exception as e:
            logger.error(f"Error getting recent interactions: {e}")
            return []

    # Stub methods to prevent breaking bot - will implement with friends/conversations tables

    def update_friend_profile(self, username: str, interaction_type: str, success: bool, engagement_data: Dict[str, Any]):
        """Stub - will implement with friends table"""
        pass

    def get_friend_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Stub - will implement with friends table"""
        return None

    def update_strategy(self, strategy_type: str, success: bool, context: Dict[str, Any]):
        """Stub - strategies removed from current phase"""
        pass

    def get_strategy_effectiveness(self, strategy_type: str) -> Optional[Dict[str, Any]]:
        """Stub - strategies removed from current phase"""
        return None

    def update_context(self, context_data: Dict[str, Any]):
        """Stub - context tracking not needed in current phase"""
        pass

    def get_context(self) -> Dict[str, Any]:
        """Stub - context tracking not needed in current phase"""
        return {"active_conversations": [], "session_data": {}}

    def get_successful_patterns(self, min_success_rate: float = 0.6) -> Dict[str, Any]:
        """Stub - patterns removed from current phase"""
        return {}
