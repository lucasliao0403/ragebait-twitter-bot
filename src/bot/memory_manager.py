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

        # Create indexes for fast queries on interactions
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_author ON interactions(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(type)')

        # Create friends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                username TEXT PRIMARY KEY,
                last_interaction TEXT,
                interaction_count INTEGER DEFAULT 0
            )
        ''')

        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                tweets TEXT NOT NULL,
                participants TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')

        # Create index for conversations
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(last_updated)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_thread ON conversations(thread_id)')

        conn.commit()
        conn.close()

    def log_interaction(self, interaction_data: Dict[str, Any]):
        """Log an interaction to SQLite database"""
        try:
            print(f"\n[MemoryManager] Logging interaction: type={interaction_data.get('type')}, author={interaction_data.get('author')}")
            print(f"[MemoryManager] Full interaction_data: {interaction_data}")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build metadata from extra fields
            metadata = {}
            if 'search_query' in interaction_data:
                metadata['search_query'] = interaction_data['search_query']
            if 'tweet_url' in interaction_data:
                metadata['target_url'] = interaction_data['tweet_url']

            metadata_json = json.dumps(metadata) if metadata else None

            # Get URL from either 'url' or 'tweet_url' field
            url = interaction_data.get('url') or interaction_data.get('tweet_url')

            print(f"[MemoryManager] Saving to DB: url={url}, content={interaction_data.get('text')[:50] if interaction_data.get('text') else None}...")

            # Insert interaction with parameterized query to prevent SQL injection
            cursor.execute('''
                INSERT INTO interactions (timestamp, type, content, author, url, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                interaction_data.get('type'),
                interaction_data.get('text'),  # 'text' field maps to 'content' column
                interaction_data.get('author'),
                url,
                metadata_json
            ))

            row_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"[MemoryManager] ✓ Successfully saved interaction to database (id={row_id})\n")

            # Update friend profile if this is reading someone's tweet
            author = interaction_data.get('author')
            if author and interaction_data.get('type') in ['timeline_read', 'search_result', 'user_tweets_read']:
                self.update_friend_profile(author)

        except Exception as e:
            print(f"[MemoryManager] ❌ Error logging interaction to database: {e}")
            print(f"[MemoryManager] Interaction data: {interaction_data}")
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

    def update_friend_profile(self, username: str, interaction_type: str = None, success: bool = None, engagement_data: Dict[str, Any] = None):
        """Update friend profile - tracks interaction count and last interaction time"""
        try:
            # Skip if no username (e.g., self interactions)
            if not username or username == 'self':
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if friend exists
            cursor.execute('SELECT username, interaction_count FROM friends WHERE username = ?', (username,))
            existing = cursor.fetchone()

            timestamp = datetime.now().isoformat()

            if existing:
                # Update existing friend
                new_count = existing[1] + 1
                cursor.execute('''
                    UPDATE friends
                    SET last_interaction = ?, interaction_count = ?
                    WHERE username = ?
                ''', (timestamp, new_count, username))
            else:
                # Insert new friend
                cursor.execute('''
                    INSERT INTO friends (username, last_interaction, interaction_count)
                    VALUES (?, ?, 1)
                ''', (username, timestamp))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[MemoryManager] ❌ Error updating friend profile: {e}")

    def get_friend_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get friend profile data"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM friends WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            print(f"[MemoryManager] ❌ Error getting friend profile: {e}")
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

    def log_conversation(self, thread_id: str, original_tweet: Dict[str, Any], reply_tweet: Dict[str, Any]):
        """Log a conversation when replying to a tweet"""
        try:
            print(f"\n[MemoryManager] Logging conversation for thread: {thread_id}")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build tweets array with both original and reply
            tweets = [
                {
                    "author": original_tweet.get('author', 'unknown'),
                    "text": original_tweet.get('text', ''),
                    "url": original_tweet.get('url', thread_id),
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "author": "self",
                    "text": reply_tweet.get('text', ''),
                    "url": thread_id,  # Reply URL is same as thread
                    "timestamp": datetime.now().isoformat()
                }
            ]

            # Get unique participants
            participants = list(set([original_tweet.get('author', 'unknown'), 'self']))

            # Check if conversation already exists
            cursor.execute('SELECT id, tweets FROM conversations WHERE thread_id = ?', (thread_id,))
            existing = cursor.fetchone()

            timestamp = datetime.now().isoformat()

            if existing:
                # Append to existing conversation
                existing_tweets = json.loads(existing[1])
                existing_tweets.append(tweets[1])  # Only add the new reply
                cursor.execute('''
                    UPDATE conversations
                    SET tweets = ?, last_updated = ?
                    WHERE thread_id = ?
                ''', (json.dumps(existing_tweets), timestamp, thread_id))
                print(f"[MemoryManager] Updated existing conversation (id={existing[0]})")
            else:
                # Create new conversation
                cursor.execute('''
                    INSERT INTO conversations (thread_id, tweets, participants, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (thread_id, json.dumps(tweets), json.dumps(participants), timestamp))
                print(f"[MemoryManager] Created new conversation (id={cursor.lastrowid})")

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[MemoryManager] ❌ Error logging conversation: {e}")
