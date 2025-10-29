# Ragebait Twitter Bot

## Overview

An agentic Twitter bot to ragebait tech twitter.

Built using browser-use and tweety-ns.

## Core Functionality

**Browser Automation:**
- Session-based Twitter interaction through headless browser
- Natural navigation and content creation
- Authentication with 2FA support and session persistence

**Social Intelligence:**
- Post tweets and replies with context awareness
- Read timelines and analyze friend content
- Search for relevant conversations and trends
- Reply to ongoing discussions with appropriate tone

**Memory & Learning:**
- Track friend communication preferences and styles
- Monitor engagement metrics and relationship health
- Learn optimal timing and content strategies
- Maintain conversation context across sessions

## Memory Architecture

**Stage 1: Basic Browser Agent**
Simple automated Twitter interactions with session management.

**Stage 2: JSON Memory System**
- Recent interactions tracking
- Friend preference storage
- Basic engagement metrics
- Conversation context logging

**TODO:**
- implement RAG
    - remove hard coded rag examples (remove from DB as well)
    - find ~100 high quality tweet examples
- implement fully autonomous workflow for reply generation
- improve consistency of browser use functions:
    - post tweet doesn't always stop
    - login doesn't always work
- check out cerebras
- clean up (de-slopify) documentation
- clean up logging
- host chromadb somewhere so it doesn't have to initialize every time.

## Key Features

- **Persistent browser sessions** to avoid repeated logins
- **Natural timing patterns** that mimic human behavior
- **Friend-specific adaptation** based on communication history
- **Engagement tracking** for continuous improvement
- **Relationship maintenance** through authentic interactions
- **Content strategy evolution** based on success metrics

## Safety & Ethics

- Conservative rate limiting and natural interaction patterns
- Focus on tech discussions, coding culture, and professional banter
- Relationship-first approach with genuine engagement
- Account protection through browser-based authentication
- Manual oversight and approval workflows
