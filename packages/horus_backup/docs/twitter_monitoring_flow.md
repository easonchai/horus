# Twitter Monitoring Process Flow

This document provides a detailed explanation of the Twitter monitoring feature in the Horus security agent.

## Overview

The Twitter monitoring feature automatically scans tweets from trusted security accounts for cryptocurrency security threats. When a potential threat is detected, it is analyzed and processed by the Horus security agent, which can then take appropriate actions to protect the user's assets.

## Process Flow Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │     │                 │
│  Fetch Tweets   │────▶│ Filter Relevant │────▶│ Analyze Tweets  │────▶│ Format Security │
│  from Trusted   │     │     Tweets      │     │  with OpenAI    │     │     Alerts      │
│    Sources      │     │                 │     │                 │     │                 │
│                 │     │                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                                                │
                                                                                │
                                                                                ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │     │                 │
│  Execute Action │◀────│  Generate Action│◀────│ Process Security│◀────│   Send Alerts   │
│      Plan       │     │      Plan       │     │     Alert       │     │   to Horus      │
│                 │     │                 │     │                 │     │                 │
│                 │     │                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Detailed Process Flow

### 1. Twitter Monitoring Phase (New)

#### 1.1 Initialization
- The `TwitterSecurityMonitor` class is initialized with Twitter API credentials from environment variables
- A list of trusted security accounts is defined
- The OpenAI client is initialized for tweet analysis
- A record of the last processed tweet ID for each account is maintained to avoid processing the same tweets multiple times

#### 1.2 Fetch Tweets from Trusted Sources
- For each trusted security account, the monitor fetches the latest tweets
- If a last processed ID exists for an account, only tweets newer than that ID are fetched
- The Twitter API is accessed using the Tweepy library
- Error handling is implemented to handle API rate limits and network issues

#### 1.3 Filter Security-Relevant Tweets
- Each tweet is analyzed for security-relevant keywords
- Keywords include: "vulnerability", "exploit", "hack", "attack", "security", "breach", etc.
- Only tweets containing these keywords are passed to the next stage
- This filtering reduces the number of tweets that need to be analyzed by the more expensive OpenAI API

#### 1.4 Analyze Tweets for Security Threats
- Filtered tweets are analyzed using OpenAI's GPT-4o model
- A carefully crafted prompt asks the model to:
  - Determine if the tweet describes a real crypto security threat
  - Summarize the specific threat/vulnerability
  - Identify affected protocols, tokens, or wallets
  - Describe the potential impact and urgency level
  - Recommend potential protective actions
- The response is structured as JSON for easy parsing
- Only tweets that are confirmed as security threats by the model are passed to the next stage

#### 1.5 Format Security Alerts
- For each confirmed security threat, a formatted alert message is created
- The alert includes:
  - A summary of the threat
  - Severity and urgency levels
  - Affected systems
  - Source information (Twitter URL)
  - Timestamp
  - Original tweet text
- This format ensures that the alert contains all necessary information for the Horus security agent to process

### 2. Horus Security Agent Phase (Existing)

#### 2.1 Process Security Alert
- The formatted alert is passed to the `process_security_alert` function
- This function uses OpenAI to analyze the alert and determine the appropriate action plan
- The analysis considers:
  - The nature of the threat
  - The affected systems
  - The urgency of the situation
  - The potential impact

#### 2.2 Generate Action Plan
- Based on the analysis, an action plan is generated
- The action plan consists of a sequence of actions to take
- Each action has:
  - An action type (revoke, swap, withdrawal)
  - An explanation of why the action is needed
  - Parameters specific to the action type
- The actions are ordered in the optimal sequence for maximum security

#### 2.3 Execute Action Plan
- Each action in the plan is executed in sequence
- The execution uses the appropriate tool for each action:
  - `revoke_tool`: Revokes permissions for a token or protocol
  - `swap_tool`: Swaps vulnerable tokens for safer ones
  - `withdrawal_tool`: Withdraws funds from a compromised protocol to a safe address
- Error handling is implemented to ensure that if one action fails, the rest of the plan can still be executed

### 3. System Integration

#### 3.1 Background Thread Management
- The Twitter monitoring runs in a background thread
- This allows the main application to remain responsive for manual alert entry
- The thread periodically checks for new tweets based on a configurable interval
- A stop event is used to gracefully shut down the thread when the application exits

#### 3.2 Command-Line Interface
- Command-line arguments allow the user to:
  - Enable or disable Twitter monitoring (`--twitter`)
  - Set the check interval in seconds (`--interval`)
- If not specified via command-line, the user is prompted to enable Twitter monitoring when the application starts

#### 3.3 Environment Variables
- Twitter API credentials are stored in environment variables:
  - `TWITTER_BEARER_TOKEN`
  - `TWITTER_API_KEY`
  - `TWITTER_API_SECRET`
  - `TWITTER_ACCESS_TOKEN`
  - `TWITTER_ACCESS_TOKEN_SECRET`
- These are loaded from a `.env` file using the `python-dotenv` library

## Error Handling and Resilience

- **API Rate Limits**: The system handles Twitter API rate limits by catching exceptions and waiting before retrying
- **Network Issues**: Network connectivity issues are caught and logged without crashing the application
- **Missing Credentials**: The system checks for required environment variables and provides clear error messages if they are missing
- **Thread Exceptions**: Exceptions in the monitoring thread are caught and logged, allowing the thread to continue running
- **Graceful Shutdown**: The monitoring thread is properly shut down when the application exits

## Configuration Options

- **Check Interval**: The interval between Twitter checks can be configured (default: 300 seconds)
- **Trusted Sources**: The list of trusted security accounts can be modified in the `TwitterSecurityMonitor` class
- **Security Keywords**: The list of keywords used for filtering can be customized in the `filter_security_relevant_tweets` method

## Future Enhancements

- **Dynamic Trusted Sources**: Allow users to add or remove trusted sources at runtime
- **Sentiment Analysis**: Incorporate sentiment analysis to better identify urgent threats
- **User Notifications**: Add push notifications or email alerts for critical threats
- **Historical Analysis**: Store and analyze historical security alerts to identify patterns
- **Custom Actions**: Allow users to define custom actions for specific types of threats
