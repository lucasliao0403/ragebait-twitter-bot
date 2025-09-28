# Dynamic Twitter Bot for Tech Trend Engagement

## Core Philosophy

Build an adaptive bot that learns and responds to real-time tech Twitter trends through dynamic research and memory systems. No hard-coded behaviors - everything is discovered, learned, and evolved based on current conversations and emerging patterns.

## Key References

- **[CoALA Paper](https://arxiv.org/abs/2309.02427)**: Cognitive Architectures for Language Agents - theoretical framework for agent memory and decision-making
- **[LangGraph Documentation](https://langchain-ai.github.io/langgraph/)**: Stateful agent orchestration framework with built-in memory management
- **[LangGraph Memory Guide](https://blog.langchain.com/memory-for-agents/)**: Comprehensive guide to implementing CoALA memory types in production
- **[Twikit Documentation](https://twikit.readthedocs.io/en/latest/)**: Free Twitter API scraper with no API key requirements
- **[Twikit GitHub](https://github.com/d60/twikit)**: Examples and rate limit guidelines for account safety

## Installation

```bash
pip install twikit langgraph langchain openai asyncpg
```

## Configuration

Create `config.ini`:
```ini
[TWITTER]
username = your_twitter_username
email = your_twitter_email
password = your_twitter_password

[OPENAI]
api_key = your_openai_api_key

[DATABASE]
connection_string = postgresql://user:password@localhost/twitterbot

[RATE_LIMITS]
min_delay_between_requests = 5
max_requests_per_hour = 50
login_cooldown_hours = 24
```

## Account Protection Guidelines

**CRITICAL**: Twikit uses unofficial Twitter APIs. Follow these rules to avoid account suspension:

### Avoid Rate Limits
- **Minimum 5-second delays** between all requests to prevent suspicious activity detection
- **Maximum 50 requests per hour** across all operations (trends, tweets, friend analysis)
- Monitor for rate limit errors and implement exponential backoff when hit

### Cookie-Based Authentication (No Repeated Logins)
- **Login ONCE** using `login_twitter.py`, then save cookies to `cookies.json`
- **Reuse cookies** for all subsequent operations - never call login repeatedly
- **Only re-login** if cookies expire (typically 24-48 hours)

### Message Limits
- **Maximum 5-10 tweets per day** to avoid messaging scrutiny
- **Space out tweets** by at least 30 minutes between posts
- **Vary posting times** - don't tweet at exact intervals

### Content Restrictions
- **Avoid sensitive content**: No politics, discrimination, hate speech, violence, or sexual content
- **Keep it tech-focused**: Framework debates, coding jokes, professional banter only
- **Stay within community guidelines**: Friendly roasting, not harassment

## Manual Commands

### Initial Setup (Rate-Limited)
```bash
python3 setup_database.py
python3 login_twitter.py  # Only run ONCE - saves cookies to cookies.json
```

**⚠️ IMPORTANT**: After first login, `login_twitter.py` will automatically use saved cookies. Never run repeated logins.

### Manual Operations

**Analyze Friends (Rate-Limited)**
```bash
python3 analyze_friends.py --friends="friend1,friend2,friend3" --delay=5
```
- **Rate Limiting**: 5-second minimum delay between `client.get_user_tweets()` calls
- **Max Friends**: Analyze max 10 friends per hour to stay under request limits
- GPT-4o analyzes communication styles, interests, current tech opinions
- Updates Network Memory table with friend behavioral patterns

**Update Trends (Rate-Limited)** 
```bash
python3 update_trends.py --delay=10
```
- **Rate Limiting**: 10-second delay after `client.get_trends()` call
- **Frequency**: Run maximum once every 30 minutes to avoid suspicion
- GPT-4o categorizes tech-related trends vs noise
- Updates Trend Memory table with topic, sentiment, timestamps

**Generate Responses (Safe)**
```bash
python3 generate_responses.py --count=30 --delay=3
```
- **Rate Limiting**: 3-second delay between timeline requests
- **Safety**: Only generates responses, doesn't post anything
- GPT-4o analyzes which tweets to reply to based on friend context and trend alignment
- Generates potential responses using CoALA memory hierarchy
- Displays proposed tweets/replies for manual approval

**Post Approved Content (HEAVILY RATE-LIMITED)**
```bash
python3 post_responses.py --file="proposed_responses.json" --max-posts=3 --spacing=30min
```
- **CRITICAL LIMITS**: Maximum 3 posts per execution, 30-minute minimum spacing
- **Daily Limit**: Never exceed 5-10 total posts per day
- Posts approved tweets using `client.create_tweet()`
- Updates Context Memory with posted content for tracking
- **Automatic delays** prevent rapid-fire posting

**Measure Success (Rate-Limited)**
```bash
python3 measure_engagement.py --hours=24 --delay=5
```
- **Rate Limiting**: 5-second delay between tweet fetch requests
- Fetches your recent tweets posted in last 24 hours
- Counts likes, replies, retweets for each tweet
- Uses GPT-4o to analyze reply sentiment and feedback
- Updates Pattern Memory with success/failure patterns

## Dynamic Learning Architecture

### Real-Time Pattern Discovery

The bot continuously analyzes current tech discourse through manual triggers to identify:
- Emerging technology discussions and sentiment shifts via `update_trends.py`
- Friend communication patterns and preferences via `analyze_friends.py` 
- Successful engagement strategies via `measure_engagement.py`
- Viral content formats and community reactions through trend analysis

### Adaptive Memory System with CoALA + LangGraph

Implement CoALA's cognitive architecture using LangGraph's stateful framework and a unified PostgreSQL database for all memory types.

#### CoALA Memory Architecture

**Working Memory (LangGraph State)**
- Current conversation context loaded during `generate_responses.py`
- Active reasoning process for response selection
- Real-time trend data being processed by GPT-4o

**Long-Term Memory (PostgreSQL + pgvector)**
- **Episodic Memory**: Sequences of past successful/failed interactions stored by `measure_engagement.py`
- **Semantic Memory**: Factual knowledge about friends, trends, and patterns from `analyze_friends.py` and `update_trends.py`
- **Procedural Memory**: Learned strategies and response templates refined through success measurement

#### Memory Types and Storage Strategy

**Trend Memory Table**: Time-sensitive data populated by `update_trends.py`
- Topic names, sentiment scores, engagement metrics
- Expiration timestamps for automatic cleanup of stale trends
- Tech relevance classification from GPT-4o analysis

**Pattern Memory Table**: Engagement strategies learned from `measure_engagement.py`
- Response types with vector embeddings for semantic search
- Success rates, usage counts, performance tracking over time
- A/B testing results for different response styles

**Network Memory Table**: Friend behaviors populated by `analyze_friends.py`
- Communication styles, interests, boundaries for each friend
- Relationship strength scores based on interaction history
- Current tech framework preferences and opinion patterns

**Context Memory Table**: Conversation histories from `generate_responses.py`
- Thread IDs, participant lists, conversation context
- Posted responses and their engagement outcomes
- Reply chains and conversation evolution tracking

#### LangGraph Implementation Architecture

**Agent Foundation**: LangGraph's create_react_agent with PostgresSaver checkpointer using GPT-4o for all reasoning and decision-making processes.

**Memory Manager**: Custom memory interface handling CRUD operations across all four memory types with consistency and performance optimization.

**CoALA-Inspired Tools**: 
- `read_trends()` - Query Trend Memory for current viral topics
- `analyze_patterns()` - Search Pattern Memory for successful engagement strategies
- `recall_friend_context()` - Retrieve Network Memory for specific friend relationships
- `post_tweet()` - Execute `client.create_tweet()` through Twikit
- `learn_from_interaction()` - Update all memory types based on engagement results

**Decision Loop**: CoALA's planning and execution cycle integrated into response generation process with reasoning, retrieval, and action selection phases.

## Real-Time Trend Monitoring

### Automated Data Sources via Manual Triggers

**Trending Topics via `update_trends.py`**
- Calls `client.get_trends('trending')` for current Twitter trending hashtags
- GPT-4o filters for tech-related discussions and emerging framework debates
- Stores trend lifecycle data with sentiment analysis and engagement potential

### Dynamic Pattern Recognition via `analyze_friends.py`

**Friend Behavior Analysis**
- `client.get_user_tweets(friend_handle, count=50)` for recent tweet history
- GPT-4o identifies tweet frequency patterns, engagement styles, current interests
- Tracks framework preferences, career updates, communication tone shifts
- Detects opinion changes and technical focus areas over time

### Intelligent Content Analysis

**Sentiment Analysis**: GPT-4o tracks emotional patterns in friend tweets and trending discussions
**Topic Clustering**: Groups related conversations to identify mega-trends in tech discourse  
**Influence Mapping**: Identifies opinion leaders through engagement metrics and reply patterns
**Meme Lifecycle Tracking**: Monitors viral content evolution from emergence to saturation
**Counter-Narrative Detection**: Finds contrarian viewpoints for engaging response opportunities

## Dynamic Response Generation

### Context-Aware Content Creation via `generate_responses.py`

Generate responses using CoALA's memory hierarchy through LangGraph state management:

**Current Conversation Context**: Working memory from timeline analysis (last 30 tweets)
**Historical Patterns**: Episodic memory of successful interaction sequences from Pattern Memory
**Trend Alignment**: Semantic memory of current viral topics from Trend Memory  
**Personality Adaptation**: Procedural memory of learned response strategies
**Friend-Specific Context**: Network memory of individual relationship dynamics and preferences

### Response Strategy Evolution

**Success Pattern Recognition**: `measure_engagement.py` identifies high-engagement response types using like/reply/retweet metrics
**Failure Analysis**: GPT-4o analyzes low-engagement posts and negative reply sentiment to avoid repeated mistakes
**Style Adaptation**: Evolution of communication patterns based on engagement feedback stored in Pattern Memory
**Contextual Awareness**: Decision logic for engagement timing and target selection based on friend activity patterns

### Memory-Driven Personalization

**Friend-Specific History**: Tailored responses based on individual relationship data in Network Memory
**Running Joke Evolution**: Development of personalized recurring themes tracked in Context Memory
**Interest Tracking**: Focus on topics generating highest friend engagement based on historical analysis
**Boundary Recognition**: Learned comfort zones and sensitive topics stored in Network Memory
**Relationship Dynamics**: Intimacy level adaptation based on friendship depth scores and interaction history

### CoALA Decision-Making Process

**Planning Phase (`generate_responses.py`)**:
1. Agent loads current timeline context (30 tweets) into working memory
2. Retrieval actions query all memory types for relevant context
3. Reasoning actions analyze friend preferences, trend alignment, and successful patterns
4. Candidate responses generated with justification based on memory insights

**Execution Phase (`post_responses.py`)**:
1. Manual approval of generated responses with explanations
2. Selected grounding action executes `client.create_tweet()` via Twikit
3. Context Memory updated with posted content and metadata

**Memory Updates (`measure_engagement.py`)**:
1. Episodic memory storage of complete interaction sequences
2. Pattern memory analysis updates successful/failed strategy classifications  
3. Network memory adjustments based on friend engagement and feedback analysis

## Command Workflow Examples

### Daily Bot Operation (Account-Safe)
```bash
# Morning routine - SPACED OUT to avoid rate limits
python3 update_trends.py --delay=10
sleep 300  # 5-minute break
python3 analyze_friends.py --friends="friend1,friend2" --delay=5
sleep 600  # 10-minute break

# Generate and review responses (safe - no API calls)
python3 generate_responses.py --count=30 --delay=3
# Review proposed_responses.json, edit as needed
# CRITICAL: Wait 30+ minutes before posting
python3 post_responses.py --file="proposed_responses.json" --max-posts=2 --spacing=45min

# Evening analysis - learn from the day (after 4+ hours)
python3 measure_engagement.py --hours=24 --delay=5
```

**⚠️ ACCOUNT SAFETY NOTES**:
- **Never run commands back-to-back** - always include sleep delays
- **Maximum 2-3 posts per day** to avoid messaging scrutiny  
- **Wait 4+ hours** between major operations (analyze → post → measure)
- **Monitor rate limits** - if you hit limits, wait 24 hours before retrying

### Weekly Learning Cycle (Ultra-Conservative)
```bash
# Sunday: Comprehensive friend analysis (SLOW)
python3 analyze_friends.py --friends="all" --deep-analysis --delay=10 --max-friends=5

# Wednesday: Pattern analysis (database-only, safe)
python3 analyze_patterns.py --timeframe="week"

# Saturday: Memory cleanup (database-only, safe)  
python3 optimize_memory.py

# NEVER run weekly commands on same day as daily posting
```

## Success Metrics

### Engagement Goals Measured by `measure_engagement.py`

**Quantitative Metrics**:
- Like counts per tweet compared to baseline
- Reply engagement rates and sentiment analysis
- Retweet distribution and reach metrics
- Friend-specific interaction rates and response patterns

**Qualitative Analysis via GPT-4o**:
- Reply sentiment classification (positive/negative/neutral feedback)
- Conversation thread quality and depth analysis
- Relationship maintenance effectiveness scores
- Community reception and integration measurement

## Long-term Learning Strategy

### Memory System Optimization

**PostgreSQL Performance**: Query optimization across memory tables with strategic indexing and connection pooling managed through database maintenance commands
**Vector Search Efficiency**: pgvector semantic similarity searches in Pattern Memory for response strategy matching  
**Data Retention Strategies**: Automated cleanup of expired trends and low-value interactions via scheduled cleanup commands
**Pattern Generalization**: GPT-4o extraction of abstract principles from specific successful interactions stored in Episodic Memory
**Cross-Memory Learning**: Application of successful strategies across different friend contexts using Network Memory insights

### Adaptive Architecture

**Real-time Model Updates**: Continuous refinement of response generation based on engagement feedback from `measure_engagement.py`
**Dynamic Personality Adjustment**: Evolution of bot character based on community reception using Procedural Memory updates
**Context Window Expansion**: Increasingly sophisticated conversation history maintenance in Context Memory
**Emergent Behavior Discovery**: Recognition of unexpected successful traits through Pattern Memory evolution analysis

### System Performance Monitoring via `system_stats.py`

**Memory Performance Metrics**:
- Query response times across different memory table types
- Vector search accuracy and relevance scoring in Pattern Memory  
- Memory usage patterns and storage optimization opportunities
- Cache hit rates and database connection pool efficiency

**Bot Performance Correlation**:
- Engagement rate correlation with Trend Memory freshness
- Response quality correlation with Pattern Memory accuracy
- Relationship maintenance effectiveness using Network Memory insights  
- Overall learning velocity through Episodic Memory accumulation analysis

## Technical Infrastructure

### Database Architecture
Single PostgreSQL instance with pgvector extension handling all memory types, LangGraph checkpoints, and performance optimization through strategic indexing and connection pooling.

### Model Integration  
GPT-4o integration through OpenAI API with proper key management and fallback strategies for reliability across all analysis and generation commands.

### State Management
LangGraph's built-in state persistence combined with custom memory management for specialized Twitter bot functionality and cross-session learning.

### Twikit Integration with Account Protection
All Twitter interactions through Twikit library with:
- **Cookie persistence** via cookies.json (no repeated logins)
- **Built-in rate limit handling** with exponential backoff
- **Request spacing** enforcement to prevent suspicious activity patterns
- **Daily/hourly request quotas** to stay under Twitter's radar

## Boundaries and Ethics

### Keep It Light
- Focus on ideas and behaviors, not personal attacks
- Avoid sensitive topics like job searches or failures  
- Don't target genuine struggles or learning moments
- Maintain plausible deniability as "just joking"

### Relationship Maintenance
- Occasionally compliment genuinely good content
- Acknowledge when proven wrong
- Vary targets so no single friend feels picked on
- Be prepared to explain jokes if they don't land

## Best Practices & Production Tips

### Development Workflow
1. **Start Small**: Begin with 2-3 close friends who know about the bot
2. **Test Offline**: Use `generate_responses.py` extensively before posting anything
3. **Manual Approval**: Always review generated content before posting
4. **Monitor Engagement**: Track both positive and negative feedback patterns
5. **Iterate Slowly**: Make small changes based on success metrics

### Memory Management
- **Regular Cleanup**: Run `optimize_memory.py` weekly to prevent database bloat
- **Pattern Analysis**: Use `analyze_patterns.py` to identify successful strategies
- **Friend Segmentation**: Group friends by communication style for better targeting
- **Trend Filtering**: Focus on tech trends with high engagement potential
- **Context Preservation**: Maintain conversation threads for coherent interactions

### Operational Security
- **Separate Accounts**: Consider using a dedicated bot account vs personal account
- **Rate Limit Monitoring**: Watch for 429 errors and implement exponential backoff
- **Cookie Rotation**: Refresh login cookies weekly to maintain session health
- **Error Handling**: Implement robust retry logic with increasing delays
- **Logging**: Track all API calls and response times for debugging

### Content Strategy
- **Tech Focus**: Stay within programming, frameworks, and developer culture
- **Timing Optimization**: Post during peak friend activity hours
- **Engagement Variety**: Mix original tweets, replies, and quote tweets
- **Personality Consistency**: Maintain recognizable voice across all interactions
- **Community Building**: Foster discussions rather than just dropping jokes

### Scaling Considerations
- **Database Indexing**: Optimize queries as memory tables grow
- **Parallel Processing**: Use async operations for friend analysis
- **Caching Strategy**: Cache frequently accessed friend and trend data
- **Memory Limits**: Set retention policies for old episodic memories
- **Performance Monitoring**: Track response times and memory usage patterns

### Troubleshooting Common Issues
- **Rate Limits**: If hit, wait 24 hours before resuming operations
- **Login Failures**: Delete cookies.json and re-run login_twitter.py once
- **Low Engagement**: Analyze Pattern Memory for successful response types
- **Friend Complaints**: Check Network Memory for boundary violations
- **Database Errors**: Run database integrity checks and repair scripts

For more detailed implementation guidance, see the [LangGraph Memory Documentation](https://blog.langchain.com/memory-for-agents/) and [Twikit Best Practices](https://github.com/d60/twikit/blob/main/ratelimits.md).