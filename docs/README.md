# Ragebait Twitter Bot

## Overview

An agentic Twitter bot to ragebait tech twitter.

## Tech Stack:
- tweety-ns
- browser-use
- anthropic
- chromadb 
- gemini

## Functionality
1) Read timeline using tweety-ns
2) Add interesting tweets and their replies to /.rag_data for RAG. Tweets are stored by author.
3) TODO: Actively read timeline and select tweets to reply to. Cron job maybe?
4) Logs interactions (timeline reads, replies, etc.) in /data/memory.db
5) Replying: 
    1) Build reply context: author tweets + relevant RAG tweets and their replies
    2) Determine appropriate tone to reply with using Gemini
    3) Generate and post reply using Claude Opus 
- TODO: Tracks engagement and personalizes interactions to increase engagement.




