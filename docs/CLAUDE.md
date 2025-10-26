# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPLEMENTATION INSTRUCTIONS

- When implementing features, implement exactly the minimum and no more. No testing or examples unless otherwise specified.
- When modifying prompts, add/remove minimal amount of text to achieve desired effect. Do not modify any other text.
- If importing any new packages, make sure to update /requirements.txt
- NEVER read .env files

## Project Overview

This is a Dynamic Twitter Bot for Tech Trend Engagement that uses tweety-ns for Twitter API interaction and adaptive learning through CoALA memory architecture. The bot interacts with Twitter through the tweety-ns library (reverse-engineered Twitter API) and learns from interactions to improve engagement strategies.

## Key References

**IMPORTANT**: Claude Code should refer to these links whenever implementing features or troubleshooting issues:

- **[CoALA Paper](https://arxiv.org/html/2309.02427v3#S4)**: Cognitive Architectures for Language Agents - theoretical framework for memory architecture implementation
- **[tweety-ns GitHub](https://github.com/mahrtayyab/tweety)**: Twitter interaction library documentation, examples, and API reference
- **[tweety-ns Documentation](https://mahrtayyab.github.io/tweety_docs/)**: Full documentation for tweety-ns library

## Coding Practices (IMPORTANT)

- When implementing features, implement exactly the minimum and no more. No testing or examples unless otherwise specified.
- If importing any new packages, make sure to update /requirements.txt

## Implementation Stages

### Stage 1: Twitter API Bot (Current Implementation)
**Goal:** Direct Twitter interaction bot using tweety-ns library

**Environment Setup:**
```bash
pip install tweety-ns anthropic python-dotenv chromadb openai
```

**Environment Variables (.env):**
```
ANTHROPIC_API_KEY=your_anthropic_api_key
TWITTER_USERNAME=your_twitter_username
TWITTER_PASSWORD=your_twitter_password
OPENAI_API_KEY=your_openai_api_key  # For RAG embeddings
```

**Core Files:**
- `twitter_tweety_bot.py` - Main bot class using tweety-ns
- `memory_manager.py` - SQLite-based memory system
- `style_rag.py` - RAG system for style-based reply generation
- `reply_prompt.txt` - Bot personality and behavior prompt for AI reply generation
- `test_bot.py` - Simple CLI for manual testing
- `import_tweets.py` - Script to import style tweets into RAG

**Functionality:**
- `start_session()` - Authenticate with Twitter (session-based, no repeated logins)
- `post_tweet(text)` - Post a tweet via API
- `get_timeline(count=10)` - Read home timeline (returns structured data)
- `get_user_tweets(username, count=10)` - Get specific user's tweets
- `generate_reply(tweet_url)` - Generate AI reply using Claude 4.5 Sonnet (Core Feature)
- `reply_to_tweet(tweet_url, text)` - Reply to tweets
- `search_tweets(query, count=10)` - Search functionality with filters
- `close_session()` - Clean up session

**Session Management:**
- Session-based authentication with tweety-ns
- Automatic session persistence (no manual save needed)
- 2FA support during initial login
- Simple error handling (log and exit)

**AI Reply Generation (Core Feature):**
- `generate_reply(tweet_url)` - Generates contextual replies using Claude 4.5 Sonnet
- System prompt in `/src/bot/reply_prompt.txt` defines bot personality
- Memory-aware: Learns from previous tweets by the same author to match their style
- RAG-enhanced: Uses ChromaDB to retrieve similar style tweets for context
- Context-aware: Fetches tweet details via tweety-ns before generating reply
- Engagement-optimized: Designed to create ragebait/satirical takes for maximum engagement
- CLI supports both AI-generated and manual replies with preview/confirmation
- Uses tweety-ns for Twitter API calls, Claude 4.5 Sonnet for content generation

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


**FUTURE FEATURE:** host chromadb somewhere so it doesn't have to initialize every time.

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
  - Product announcements
  - Polarizing statements about tech
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

## Twitter API Interaction Details (tweety-ns)

### Session Lifecycle
```
start_session() → authenticate_with_twitter() → [perform_operations()] → close_session()
```

**Session Persistence:**
- tweety-ns automatically saves session to `twitter_session` file
- No repeated logins needed between runs
- Session loaded automatically on next run

### Error Handling
- Authentication failures: Prompt for 2FA if needed, then retry
- Rate limits: tweety-ns handles Twitter rate limits automatically
- API errors: Log error with details and exit gracefully
- Tweet not found: Handle exception and log warning

### Rate Limiting
- tweety-ns respects Twitter's rate limits internally
- Add 2-3 second delays between batch operations
- Monitor for rate limit exceptions and pause if needed
- "Abusing tweety can lead to read_only Twitter account" - use conservatively

### Key Advantages over Browser Automation
- 10-100x faster (no browser overhead)
- More reliable (no UI changes breaking functionality)
- Structured data returned (no parsing needed)
- Native async support
- Session persistence built-in

## Content Guidelines

### Prohibited Content
- Politics, hate speech, violence, sexual content

## Testing Workflow

1. **Stage 1:** Test basic Twitter API operations using `python scripts/test_bot.py`
   - Verify authentication and session persistence
   - Test posting tweets, reading timeline, replying
   - Validate AI reply generation with Claude
2. **Stage 2:** Verify memory storage and retrieval
   - Check SQLite database for logged interactions
   - Verify friend profiles are tracked
3. **Stage 3:** Test memory-driven decision making
   - Ensure previous tweets inform reply generation
   - Validate RAG system retrieves relevant style examples
4. **Stage 4:** Monitor learning and adaptation
   - Track engagement patterns over time
   - Review strategy adjustments

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Set up `.env` file with credentials in `config/.env`
3. Run test CLI: `python scripts/test_bot.py`
4. Choose option 1 to authenticate (only needed once)
5. Use options 2-6 to test functionality