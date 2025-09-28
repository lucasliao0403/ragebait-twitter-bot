import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class MemoryManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.interactions_file = os.path.join(data_dir, "interactions.json")
        self.friends_file = os.path.join(data_dir, "friends.json")
        self.strategies_file = os.path.join(data_dir, "strategies.json")
        self.context_file = os.path.join(data_dir, "context.json")

        self._init_files()

    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        files = {
            self.interactions_file: [],
            self.friends_file: {},
            self.strategies_file: {},
            self.context_file: {"active_conversations": [], "session_data": {}}
        }

        for file_path, default_data in files.items():
            if not os.path.exists(file_path):
                self._save_json(file_path, default_data)

    def _load_json(self, file_path: str) -> Any:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _save_json(self, file_path: str, data: Any):
        """Save data to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def is_promotional_content(self, tweet_text: str, author: str, indicators: List[str]) -> bool:
        """Detect if content is promotional/ad content"""
        ad_markers = ["Promoted", "Ad", "Sponsored", "Learn more"]
        promoted_indicators = ["Promoted by", "Sponsored content"]

        # Check text for ad markers
        for marker in ad_markers:
            if marker in tweet_text or marker in indicators:
                return True

        # Check for promoted tweet indicators
        for indicator in promoted_indicators:
            if indicator in indicators:
                return True

        return False

    def log_interaction(self, interaction_data: Dict[str, Any]):
        """Log an interaction (excluding ads)"""
        if self.is_promotional_content(
            interaction_data.get('text', ''),
            interaction_data.get('author', ''),
            interaction_data.get('indicators', [])
        ):
            # Log ad for completeness but don't process for learning
            self._log_promotional_content(interaction_data)
            return

        interactions = self._load_json(self.interactions_file) or []

        interaction_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_data.get('type'),
            "content": interaction_data.get('text'),
            "author": interaction_data.get('author'),
            "success": interaction_data.get('success', False),
            "engagement_metrics": interaction_data.get('engagement_metrics', {}),
            "tweet_id": interaction_data.get('tweet_id')
        }

        interactions.append(interaction_entry)
        self._save_json(self.interactions_file, interactions)

    def _log_promotional_content(self, ad_data: Dict[str, Any]):
        """Log promotional content separately (for completeness, not learning)"""
        ad_log_file = os.path.join(self.data_dir, "ads.json")
        ads = self._load_json(ad_log_file) or []

        ad_entry = {
            "timestamp": datetime.now().isoformat(),
            "content": ad_data.get('text'),
            "author": ad_data.get('author'),
            "ad_type": "promoted",
            "indicators": ad_data.get('indicators', [])
        }

        ads.append(ad_entry)
        self._save_json(ad_log_file, ads)

    def update_friend_profile(self, username: str, interaction_type: str, success: bool, engagement_data: Dict[str, Any]):
        """Update friend profile based on interaction (organic content only)"""
        friends = self._load_json(self.friends_file) or {}

        if username not in friends:
            friends[username] = {
                "preferences": {},
                "communication_style": "unknown",
                "successful_interactions": 0,
                "total_interactions": 0,
                "last_interaction": None,
                "engagement_history": []
            }

        friend_profile = friends[username]
        friend_profile["total_interactions"] += 1
        friend_profile["last_interaction"] = datetime.now().isoformat()

        if success:
            friend_profile["successful_interactions"] += 1

        # Track engagement patterns
        if interaction_type not in friend_profile["preferences"]:
            friend_profile["preferences"][interaction_type] = {"success_rate": 0, "count": 0}

        pref = friend_profile["preferences"][interaction_type]
        pref["count"] += 1
        if success:
            pref["success_rate"] = (pref["success_rate"] * (pref["count"] - 1) + 1) / pref["count"]
        else:
            pref["success_rate"] = (pref["success_rate"] * (pref["count"] - 1)) / pref["count"]

        # Store engagement data
        friend_profile["engagement_history"].append({
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "success": success,
            "engagement": engagement_data
        })

        # Keep only last 50 engagement records per friend
        if len(friend_profile["engagement_history"]) > 50:
            friend_profile["engagement_history"] = friend_profile["engagement_history"][-50:]

        friends[username] = friend_profile
        self._save_json(self.friends_file, friends)

    def get_friend_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get friend profile data"""
        friends = self._load_json(self.friends_file) or {}
        return friends.get(username)

    def update_strategy(self, strategy_type: str, success: bool, context: Dict[str, Any]):
        """Update strategy effectiveness"""
        strategies = self._load_json(self.strategies_file) or {}

        if strategy_type not in strategies:
            strategies[strategy_type] = {
                "success_count": 0,
                "total_count": 0,
                "success_rate": 0,
                "contexts": []
            }

        strategy = strategies[strategy_type]
        strategy["total_count"] += 1

        if success:
            strategy["success_count"] += 1

        strategy["success_rate"] = strategy["success_count"] / strategy["total_count"]

        # Store context for pattern analysis
        strategy["contexts"].append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "context": context
        })

        # Keep only last 100 contexts per strategy
        if len(strategy["contexts"]) > 100:
            strategy["contexts"] = strategy["contexts"][-100:]

        strategies[strategy_type] = strategy
        self._save_json(self.strategies_file, strategies)

    def get_strategy_effectiveness(self, strategy_type: str) -> Optional[Dict[str, Any]]:
        """Get strategy effectiveness data"""
        strategies = self._load_json(self.strategies_file) or {}
        return strategies.get(strategy_type)

    def update_context(self, context_data: Dict[str, Any]):
        """Update active conversation context"""
        context = self._load_json(self.context_file) or {"active_conversations": [], "session_data": {}}
        context.update(context_data)
        self._save_json(self.context_file, context)

    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return self._load_json(self.context_file) or {"active_conversations": [], "session_data": {}}

    def get_recent_interactions(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent interactions (organic content only)"""
        interactions = self._load_json(self.interactions_file) or []
        return interactions[-count:] if interactions else []

    def get_successful_patterns(self, min_success_rate: float = 0.6) -> Dict[str, Any]:
        """Get successful engagement patterns"""
        strategies = self._load_json(self.strategies_file) or {}
        successful_strategies = {}

        for strategy_type, data in strategies.items():
            if data.get("success_rate", 0) >= min_success_rate and data.get("total_count", 0) >= 5:
                successful_strategies[strategy_type] = data

        return successful_strategies