# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPLEMENTATION INSTRUCTIONS

- When implementing features, implement exactly the minimum and no more. No testing or examples unless otherwise specified.
- If importing any new packages, make sure to update /requirements.txt

## Project Overview

This is a Dynamic Twitter Bot for Tech Trend Engagement that uses browser automation via browser-use library and adaptive learning through CoALA memory architecture. The bot uses an AI agent to navigate Twitter naturally through a browser interface and learns from interactions to improve engagement strategies.

## Key References

**IMPORTANT**: Claude Code should refer to these links whenever implementing features or troubleshooting issues:

- **[CoALA Paper](https://arxiv.org/html/2309.02427v3#S4)**: Cognitive Architectures for Language Agents - theoretical framework for memory architecture implementation
- **[Browser-use GitHub](https://github.com/browser-use/browser-use)**: Browser automation library documentation, examples, and API reference

## Coding Practices (IMPORTANT)

- When implementing features, implement exactly the minimum and no more. No testing or examples unless otherwise specified.
- If importing any new packages, make sure to update /requirements.txt

## Implementation Stages

### Stage 1: Basic Browser Agent (Start Here)
**Goal:** Simple browser bot that can interact with Twitter

**Environment Setup:**
```bash
pip install browser-use anthropic python-dotenv
```

**Environment Variables (.env):**
```
ANTHROPIC_API_KEY=your_anthropic_api_key
TWITTER_USERNAME=your_twitter_username
TWITTER_PASSWORD=your_twitter_password
```

**Core Files:**
- `twitter_browser_bot.py` - Main bot class with session management
- `test_bot.py` - Simple CLI for manual testing

**Functionality:**
- `start_session()` - Open browser and login
- `post_tweet(text)` - Post a tweet
- `get_timeline(count=10)` - Read home timeline
- `get_user_tweets(username, count=10)` - Get specific user's tweets
- `reply_to_tweet(tweet_url, text)` - Reply to tweets
- `search_tweets(query, count=10)` - Search functionality
- `save_session()` - Save browser state manually
- `close_session()` - Close browser

**Session Management:**
- Persistent browser session (stays open between operations)
- Manual session save/load to avoid repeated logins
- 2FA support with manual input pause
- Simple error handling (log and exit)

### Stage 2: Basic Memory System
**Goal:** JSON-based memory to track interactions and patterns

**Additional Files:**
- `memory_manager.py` - Simple JSON storage and retrieval
- `data/` directory for memory files

**Memory Types:**
- `interactions.json` - Log of all bot interactions (excluding ads)
- `friends.json` - Friend profiles and preferences
- `strategies.json` - Basic engagement patterns
- `context.json` - Active conversation tracking

**Ad Filtering:**
- Extract ads for completeness but DO NOT process them for memory/learning
- Identify promoted tweets, sponsored content, and advertisements
- Flag content with "Promoted", "Ad", "Sponsored" labels
- Skip ads in engagement analysis and pattern recognition

**Functionality:**
- Track successful/failed interactions (organic content only)
- Store friend communication preferences (excluding ad interactions)
- Log engagement metrics (likes, replies) for real tweets only
- Basic pattern recognition (what works with whom) - ads ignored

### Stage 3: Practical Memory System
**Goal:** Lightweight social memory for realistic Twitter interactions

**Environment Setup:**
```bash
pip install sqlite3 (built-in with Python)
```

**Memory Architecture:**
- **Session Context:** Current browser state and active conversations
- **Recent Interactions:** Last 100 tweets/replies with engagement metrics
- **Friend Profiles:** Communication styles, preferences, relationship health
- **Success Patterns:** What content works, optimal timing, effective strategies

**Database Schema (SQLite):**
- `interactions` - Tweet/reply history with engagement metrics
- `friends` - Individual profiles and communication preferences
- `patterns` - Successful content types and timing data
- `conversations` - Active thread tracking and context

**Ad Filtering (Critical):**
- Extract all content including ads for data completeness
- Identify promotional content: tweets with "Promoted", "Ad", "Sponsored" indicators
- Flag advertiser accounts and sponsored content automatically
- EXCLUDE ads from all memory processing, learning, and engagement analysis

**Functionality:**
- Track engagement metrics (likes, replies, sentiment) - organic content only
- Learn friend communication preferences naturally (excluding ad interactions)
- Identify successful content patterns and timing (ads ignored)
- Maintain conversation context and relationship health (real conversations only)

### Stage 4: Simple Learning Loop
**Goal:** Basic feedback-driven improvement without over-engineering

**Functionality:**
- **Engagement Tracking:** Monitor likes, replies, unfollows for each interaction
- **Pattern Recognition:** Identify what works with specific friends and timing
- **Strategy Adjustment:** Simple rules based on clear success/failure signals
- **Relationship Monitoring:** Track friendship health and adjust approach

**Learning Process:**
```python
# After each interaction (ads filtered out)
if not is_promotional_content(tweet):
    engagement = measure_engagement(tweet_id, time_window=1hour)
    update_friend_preferences(friend_id, interaction_type, engagement)
    adjust_strategy_confidence(strategy_type, success_rate)
    maintain_relationship_score(friend_id, engagement_trend)
else:
    # Log ad for completeness but skip learning
    log_promotional_content(tweet, ad_type="promoted")
```

**Practical Features:**
- Friend-specific communication style adaptation (organic interactions only)
- Optimal timing discovery (when friends are most active/responsive)
- Content type effectiveness tracking (jokes vs support vs technical) - ads excluded
- Relationship maintenance alerts (who to check in with)

**Ad Detection Implementation:**
```python
def is_promotional_content(tweet_text, author, indicators):
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
```

## Browser Automation Details

### Session Lifecycle
```
start_session() → login_to_twitter() → [perform_operations()] → save_session() → close_session()
```

### Error Handling
- Browser crashes: Log error and exit
- Cloudflare challenges: Pause for manual intervention
- Login failures: Retry once, then exit
- 2FA prompts: Pause and wait for manual input

### Rate Limiting
- Natural browser timing (browser-use handles this)
- Conservative operation spacing
- Monitor for Twitter rate limit warnings

## Content Guidelines

### Allowed Content
- Framework debates and coding jokes
- Professional tech banter and discussions
- Developer culture references

### Prohibited Content
- Politics, discrimination, hate speech, violence, sexual content

## Testing Workflow

1. **Stage 1:** Test basic browser operations manually
2. **Stage 2:** Verify memory storage and retrieval
3. **Stage 3:** Test memory-driven decision making
4. **Stage 4:** Monitor learning and adaptation

## Safety Considerations

- Start with test account or close friends
- Monitor bot behavior closely in early stages
- Implement kill switches for runaway behavior
- Regular memory audits to prevent drift