import json
import tweepy
import time
from openai import OpenAI
import os
from datetime import datetime

class TwitterSecurityMonitor:
    """Monitors Twitter for cryptocurrency security threats."""
    
    def __init__(self, openai_client=None):
        # Initialize Twitter API client
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        if not all([bearer_token, api_key, api_secret, access_token, access_token_secret]):
            raise ValueError("Missing Twitter API credentials in environment variables")
        
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Use the provided OpenAI client or create a new one
        self.openai_client = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not self.openai_client:
            raise ValueError("Missing OpenAI API key in environment variables")
            
        self.last_processed_id = {}
        
        # List of trusted security accounts to monitor (replace with real IDs)
        self.trusted_sources = [
            "1394563210",  # Example: CertiK
            "4334324345",  # Example: PeckShield
            "2349102345"   # Example: SlowMist
        ]
    
    def get_latest_tweets(self, account_id, max_results=10):
        """Fetch the latest tweets from a specific account."""
        query_params = {'max_results': max_results}
        
        if account_id in self.last_processed_id:
            query_params['since_id'] = self.last_processed_id[account_id]
            
        try:
            tweets = self.client.get_users_tweets(
                id=account_id,
                tweet_fields=['created_at', 'conversation_id', 'public_metrics'],
                **query_params
            )
            
            if tweets.data:
                self.last_processed_id[account_id] = max(tweet.id for tweet in tweets.data)
                return tweets.data
            return []
            
        except Exception as e:
            print(f"Error fetching tweets from account {account_id}: {str(e)}")
            return []
    
    def filter_security_relevant_tweets(self, tweets):
        """Filter tweets to find those likely discussing security issues."""
        security_keywords = [
            "vulnerability", "exploit", "hack", "attack", "security", 
            "breach", "compromised", "scam", "phishing", "stolen",
            "drain", "rugpull", "emergency", "critical", "alert",
            "0day", "zero-day", "CVE", "threat", "malicious"
        ]
        
        relevant_tweets = []
        for tweet in tweets:
            if any(keyword.lower() in tweet.text.lower() for keyword in security_keywords):
                relevant_tweets.append(tweet)
                
        return relevant_tweets
    
    def analyze_threads(self, tweets):
        """Determine if tweets are discussing actual security threats."""
        if not tweets:
            return []
            
        threat_alerts = []
        
        for tweet in tweets:
            prompt = f"""
            I'm monitoring cryptocurrency security threats. Analyze this tweet:
            
            Tweet: {tweet.text}
            
            If this tweet describes a real crypto security threat, vulnerability, or hack:
            1. Summarize the specific threat/vulnerability in detail
            2. Identify affected protocols, tokens, or wallets
            3. Describe the potential impact and urgency level
            4. Recommend potential protective actions
            
            Format your response as a JSON with the following structure:
            {{
                "is_security_threat": true/false,
                "threat_details": {{
                    "summary": "summary of the threat",
                    "affected_systems": ["list", "of", "affected", "systems"],
                    "impact": "description of impact",
                    "urgency": "high/medium/low",
                    "recommended_actions": ["list", "of", "actions"]
                }}
            }}
            
            If the tweet does NOT describe a real security threat, simply return:
            {{
                "is_security_threat": false
            }}
            """
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "system", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                response_content = response.choices[0].message.content
                analysis = json.loads(response_content)
                
                if analysis.get("is_security_threat", False):
                    threat_alerts.append((tweet, analysis.get("threat_details", {})))
            except Exception as e:
                print(f"Error analyzing tweet with OpenAI: {str(e)}")
                # Create mock analysis for demonstration purposes
                if "SECURITY ALERT" in tweet.text:
                    mock_analysis = {
                        "summary": f"[MOCK ANALYSIS] {tweet.text}",
                        "affected_systems": ["Example Protocol", "Example Token"],
                        "impact": "Potential fund loss or compromise",
                        "urgency": "high",
                        "recommended_actions": [
                            "Withdraw funds immediately",
                            "Revoke permissions",
                            "Monitor wallet for suspicious activity"
                        ]
                    }
                    threat_alerts.append((tweet, mock_analysis))
                
        return threat_alerts
    
    def format_security_alert(self, tweet, threat_details):
        """Format tweet and threat analysis into a security alert message."""
        affected_systems = ", ".join(threat_details.get("affected_systems", []))
        urgency = threat_details.get("urgency", "unknown").upper()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        alert = f"""SECURITY ALERT: {threat_details.get("summary")}
        
Affected Systems: {affected_systems}
Impact: {threat_details.get("impact", "Unknown")}
Urgency: {urgency}
Timestamp: {timestamp}

Original Tweet: {tweet.text}
        
Recommended Actions:
"""
        
        for i, action in enumerate(threat_details.get("recommended_actions", []), 1):
            alert += f"{i}. {action}\n"
            
        return alert
    
    def check_all_sources(self):
        """Check all trusted sources for new security-related tweets."""
        all_security_alerts = []
        
        for source_id in self.trusted_sources:
            tweets = self.get_latest_tweets(source_id)
            relevant_tweets = self.filter_security_relevant_tweets(tweets)
            threat_alerts = self.analyze_threads(relevant_tweets)
            
            for tweet, threat_details in threat_alerts:
                security_alert = self.format_security_alert(tweet, threat_details)
                all_security_alerts.append(security_alert)
                
        return all_security_alerts
    
    def check_for_security_threats(self):
        """Check for security threats from all sources."""
        return self.check_all_sources()
