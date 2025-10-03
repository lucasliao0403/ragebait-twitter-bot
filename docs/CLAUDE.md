# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPLEMENTATION INSTRUCTIONS

- When implementing features, implement exactly the minimum and no more. No testing or examples unless otherwise specified.
- When modifying prompts, add/remove minimal amount of text to achieve desired effect. Do not modify any other text.
- If importing any new packages, make sure to update /requirements.txt
- NEVER read .env files

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
pip install browser-use groq anthropic python-dotenv
```

**Environment Variables (.env):**
```
GROQ_API_KEY=your_groq_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
TWITTER_USERNAME=your_twitter_username
TWITTER_PASSWORD=your_twitter_password
```

**Core Files:**
- `twitter_browser_bot.py` - Main bot class with session management
- `memory_manager.py` - SQLite-based memory system
- `system_prompt.txt` - Bot personality and behavior prompt for AI reply generation
- `test_bot.py` - Simple CLI for manual testing

**Functionality:**
- `start_session()` - Open browser and login
- `post_tweet(text)` - Post a tweet
- `get_timeline(count=10)` - Read home timeline
- `get_user_tweets(username, count=10)` - Get specific user's tweets
- `generate_reply(tweet_url)` - Generate AI reply using Claude 4.5 Sonnet (NEW - Core Feature)
- `reply_to_tweet(tweet_url, text)` - Reply to tweets
- `search_tweets(query, count=10)` - Search functionality
- `save_session()` - Save browser state manually
- `close_session()` - Close browser

**Session Management:**
- Persistent browser session (stays open between operations)
- Manual session save/load to avoid repeated logins
- 2FA support with manual input pause
- Simple error handling (log and exit)

**AI Reply Generation (Core Feature):**
- `generate_reply(tweet_url)` - Generates contextual replies using Claude 4.5 Sonnet
- System prompt in `/src/bot/system_prompt.txt` defines bot personality
- Memory-aware: Learns from previous tweets by the same author to match their style
- Context-aware: Analyzes the original tweet content before generating reply
- Engagement-optimized: Designed to create ragebait/controversial takes for maximum engagement
- CLI supports both AI-generated and manual replies with preview/confirmation
- Uses Groq (Llama 4 Scout) for browser automation, Claude 4.5 Sonnet for content generation

### Stage 2: Basic Memory System
**Goal:** JSON-based memory to track interactions and patterns

**Additional Files:**
- `memory_manager.py` - Simple JSON storage and retrieval
- `data/` directory for memory files

**Memory Types:**
- `interactions.json` - Log of all bot interactions
- `friends.json` - Friend profiles and preferences
- `strategies.json` - Basic engagement patterns
- `context.json` - Active conversation tracking

**Functionality:**
- Track successful/failed interactions
- Store friend communication preferences
- Log engagement metrics (likes, replies)
- Basic pattern recognition (what works with whom)

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

**Functionality:**
- Track engagement metrics (likes, replies, sentiment)
- Learn friend communication preferences naturally
- Identify successful content patterns and timing
- Maintain conversation context and relationship health

### Stage 4: Simple Learning Loop
**Goal:** Basic feedback-driven improvement without over-engineering

**Functionality:**
- **Engagement Tracking:** Monitor likes, replies, unfollows for each interaction
- **Pattern Recognition:** Identify what works with specific friends and timing
- **Strategy Adjustment:** Simple rules based on clear success/failure signals
- **Relationship Monitoring:** Track friendship health and adjust approach

**Learning Process:**
```python
# After each interaction
engagement = measure_engagement(tweet_id, time_window=1hour)
update_friend_preferences(friend_id, interaction_type, engagement)
adjust_strategy_confidence(strategy_type, success_rate)
maintain_relationship_score(friend_id, engagement_trend)
```

**Practical Features:**
- Friend-specific communication style adaptation
- Optimal timing discovery (when friends are most active/responsive)
- Content type effectiveness tracking (jokes vs support vs technical)
- Relationship maintenance alerts (who to check in with)

### Stage 5: Intelligent Tweet Selection (Future)
**Goal:** Auto-filter timeline to only reply to high-engagement-potential tweets

**Problem:** Not all tweets are worth replying to. The bot should focus on controversial, opinion-based, or shocking tweets that will generate maximum engagement when replied to.

**Selection Criteria:**
- **Reply-Worthy Tweets:**
  - Hot takes or controversial opinions
  - Bold claims or predictions
  - Polarizing statements about tech/frameworks
  - Questions that invite debate
  - Complaints or frustrations (easy targets for contrarian takes)
  - Hype or anti-hype about new tech
  - Framework/language wars
  - Strong emotional language or exaggeration

- **Skip These (Boring):**
  - Simple announcements ("Just shipped X")
  - Tutorial/educational content without opinions
  - Job postings
  - Pure factual statements
  - Retweets without commentary
  - Thread continuations (1/n, 2/n, etc.)
  - "Thank you" posts
  - Links without hot takes

**Implementation Approach:**
```python
async def filter_timeline_for_replies(self, count=50):
    """Scroll timeline and identify reply-worthy tweets"""

    # 1. Fetch timeline tweets (existing get_timeline method)
    timeline = await self.get_timeline(count)

    # 2. For each tweet, use Claude to classify as reply-worthy or not
    for tweet in timeline:
        classification = await self.classify_tweet(tweet)
        if classification['worth_replying_to']:
            # Add to reply queue with priority score
            await self.queue_reply(tweet, priority=classification['engagement_score'])

    # 3. Reply to top N tweets from queue
    return reply_queue.sorted_by_priority()[:5]
```

**Classification Function:**
- Use Claude with lightweight prompt to score tweets 0-10 for engagement potential
- Consider: controversy level, opinion strength, debate potential, emotional tone
- Fast classification (small token usage, temperature=0 for consistency)
- Store classifications in memory to improve filtering over time

**Integration with Memory:**
- Track which types of tweets historically generated most engagement when replied to
- Learn which authors consistently post reply-worthy content
- Identify topics that perform well for the bot's personality

**Benefits:**
- Focus energy on high-impact replies
- Avoid wasting API calls on boring tweets
- Increase overall engagement rate
- Build reputation for spicy, well-targeted takes

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