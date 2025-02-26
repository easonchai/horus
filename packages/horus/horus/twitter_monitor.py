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
        
        self.openai_client = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
                    "summary": "detailed description of the threat",
                    "affected_systems": ["list of affected protocols/tokens"],
                    "severity": "HIGH/MEDIUM/LOW",
                    "urgency": "IMMEDIATE/SOON/MONITOR"
                }}
            }}
            
            If this is NOT describing a real security threat, simply respond with:
            {{
                "is_security_threat": false
            }}
            
            ONLY respond with the JSON structure, nothing else.
            """
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                analysis = response.choices[0].message.content
                analysis_json = json.loads(analysis)
                
                if analysis_json.get("is_security_threat", False):
                    threat_details = analysis_json.get("threat_details", {})
                    alert = self.format_security_alert(tweet, threat_details)
                    threat_alerts.append(alert)
                    
            except Exception as e:
                print(f"Error analyzing tweet {tweet.id}: {str(e)}")
                continue
                
        return threat_alerts
    
    def format_security_alert(self, tweet, threat_details):
        """Format tweet and threat analysis into a security alert message."""
        tweet_url = f"https://twitter.com/twitter/status/{tweet.id}"
        
        alert = f"""
        SECURITY ALERT: {threat_details.get('summary', 'Unknown threat')}
        
        Severity: {threat_details.get('severity', 'UNKNOWN')}
        Urgency: {threat_details.get('urgency', 'UNKNOWN')}
        Affected Systems: {', '.join(threat_details.get('affected_systems', ['Unknown']))}
        
        Source: Twitter alert from trusted security source
        Reference: {tweet_url}
        Detected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Original Tweet: "{tweet.text}"
        """
        
        return alert.strip()
    
    def check_all_sources(self):
        """Check all trusted sources for new security-related tweets."""
        all_alerts = []
        
        for source_id in self.trusted_sources:
            tweets = self.get_latest_tweets(source_id)
            relevant_tweets = self.filter_security_relevant_tweets(tweets)
            alerts = self.analyze_threads(relevant_tweets)
            all_alerts.extend(alerts)
            
        return all_alerts
