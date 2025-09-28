# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Dynamic Twitter Bot for Tech Trend Engagement that uses adaptive learning through CoALA memory architecture and LangGraph for stateful agent orchestration. The bot learns and responds to real-time tech Twitter trends without hard-coded behaviors.

## Coding Practices (IMPORTANT)

- When implementation features, implement exactly the minimum and no more. No testing or examples unless otherwise specified.
- If importing any new packages, make sure to update /requirements.txt

## Development Commands

### Environment Setup
```bash
pip install twikit langgraph langchain openai asyncpg
python3 setup_database.py
python3 login_twitter.py  # Only run ONCE - saves cookies to cookies.json
```

### Core Operations (Rate-Limited)
```bash
# Analyze friend behavior patterns (max 10 friends per hour)
python3 analyze_friends.py --friends="friend1,friend2,friend3" --delay=5

# Update tech trends (max once every 30 minutes)
python3 update_trends.py --delay=10

# Generate responses safely (no API calls)
python3 generate_responses.py --count=30 --delay=3

# Post approved content (max 3 posts, 30-min spacing)
python3 post_responses.py --file="proposed_responses.json" --max-posts=3 --spacing=30min

# Measure engagement and learn
python3 measure_engagement.py --hours=24 --delay=5
```

### Maintenance Commands
```bash
python3 optimize_memory.py      # Weekly memory cleanup
python3 analyze_patterns.py     # Pattern analysis
python3 system_stats.py         # Performance monitoring
```

## Architecture Overview

### CoALA Memory System (PostgreSQL + pgvector)
- **Trend Memory Table**: Time-sensitive trending topics with GPT-4o tech relevance classification
- **Pattern Memory Table**: Engagement strategies with vector embeddings for semantic search
- **Network Memory Table**: Friend behaviors, communication styles, and relationship dynamics
- **Context Memory Table**: Conversation histories and thread tracking

### LangGraph Agent Framework
- **create_react_agent** with PostgresSaver checkpointer using GPT-4o
- **Memory Manager**: Custom CRUD interface across all memory types
- **CoALA-Inspired Tools**: read_trends(), analyze_patterns(), recall_friend_context(), post_tweet(), learn_from_interaction()

### Twikit Integration
- Cookie-based authentication (no repeated logins)
- Built-in rate limiting with exponential backoff
- Account protection through request spacing and daily quotas

## Critical Rate Limiting Rules

### Account Safety Requirements
- **5-second minimum delays** between all requests
- **Maximum 50 requests per hour** across all operations
- **Maximum 5-10 tweets per day** with 30+ minute spacing
- **24-hour cooldown** after hitting rate limits
- **Never run commands back-to-back** - always include sleep delays

### Authentication Protocol
- Login **ONCE** with `login_twitter.py` and save cookies to `cookies.json`
- Reuse cookies for all subsequent operations
- Only re-login if cookies expire (24-48 hours)

## Content Guidelines

### Allowed Content
- Framework debates and coding jokes
- Professional tech banter and discussions
- Developer culture references

### Prohibited Content
- Politics, discrimination, hate speech, violence, sexual content

## Development Workflow

1. **Start with `generate_responses.py`** for safe content creation
2. **Always review proposed_responses.json** before posting
3. **Use manual approval workflow** for all posts
4. **Monitor engagement** with `measure_engagement.py`
5. **Run memory cleanup weekly** with `optimize_memory.py`

## Database Schema

The system uses a single PostgreSQL instance with pgvector extension containing:
- Memory tables for CoALA architecture
- LangGraph checkpoints for state persistence
- Vector embeddings for semantic similarity search
- Performance indexes for query optimization

## Configuration Requirements

Create `config.ini` with:
- Twitter credentials (username, email, password)
- OpenAI API key for GPT-4o integration
- PostgreSQL connection string
- Rate limiting parameters (delays, request limits, cooldowns)

## Testing and Safety

- **Test offline first** using `generate_responses.py`
- **Start with 2-3 close friends** who know about the bot
- **Monitor both positive and negative feedback** patterns
- **Implement exponential backoff** for API errors
- **Track all API calls** and response times for debugging