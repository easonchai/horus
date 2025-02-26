import os
import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

# Import the TwitterSecurityMonitor class
from horus.twitter_monitor import TwitterSecurityMonitor

class TestTwitterSecurityMonitor:
    """Test suite for the TwitterSecurityMonitor class."""
    
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up mock environment variables for testing."""
        monkeypatch.setenv("TWITTER_BEARER_TOKEN", "mock_bearer_token")
        monkeypatch.setenv("TWITTER_API_KEY", "mock_api_key")
        monkeypatch.setenv("TWITTER_API_SECRET", "mock_api_secret")
        monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "mock_access_token")
        monkeypatch.setenv("TWITTER_ACCESS_TOKEN_SECRET", "mock_access_token_secret")
        monkeypatch.setenv("OPENAI_API_KEY", "mock_openai_key")
    
    @pytest.fixture
    def mock_tweet(self):
        """Create a mock tweet object for testing."""
        tweet = MagicMock()
        tweet.id = 12345
        tweet.text = "Critical security vulnerability found in DeFi protocol XYZ. Funds at risk!"
        tweet.created_at = datetime.now()
        return tweet
    
    @pytest.fixture
    def mock_openai_response(self):
        """Create a mock OpenAI response for testing."""
        response_json = {
            "is_security_threat": True,
            "threat_details": {
                "summary": "Critical vulnerability in DeFi protocol XYZ",
                "affected_systems": ["XYZ Protocol"],
                "severity": "HIGH",
                "urgency": "IMMEDIATE"
            }
        }
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps(response_json)
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        return mock_response
    
    @patch("tweepy.Client")
    @patch("openai.OpenAI")
    def test_init(self, mock_openai, mock_tweepy, mock_env_vars):
        """Test that the TwitterSecurityMonitor initializes correctly."""
        monitor = TwitterSecurityMonitor()
        
        # Check that the Twitter client was initialized with the correct credentials
        mock_tweepy.assert_called_once_with(
            bearer_token="mock_bearer_token",
            consumer_key="mock_api_key",
            consumer_secret="mock_api_secret",
            access_token="mock_access_token",
            access_token_secret="mock_access_token_secret"
        )
        
        # Check that the OpenAI client was initialized with the correct API key
        mock_openai.assert_called_once_with(api_key="mock_openai_key")
        
        # Check that the trusted sources list is not empty
        assert len(monitor.trusted_sources) > 0
    
    @patch("tweepy.Client")
    @patch("openai.OpenAI")
    def test_get_latest_tweets(self, mock_openai, mock_tweepy, mock_env_vars, mock_tweet):
        """Test that get_latest_tweets fetches tweets correctly."""
        # Set up the mock Twitter client
        mock_response = MagicMock()
        mock_response.data = [mock_tweet]
        mock_tweepy.return_value.get_users_tweets.return_value = mock_response
        
        # Initialize the monitor
        monitor = TwitterSecurityMonitor()
        
        # Call the method
        tweets = monitor.get_latest_tweets("1234567890")
        
        # Check that the Twitter client was called with the correct parameters
        mock_tweepy.return_value.get_users_tweets.assert_called_once_with(
            id="1234567890",
            tweet_fields=['created_at', 'conversation_id', 'public_metrics'],
            max_results=10
        )
        
        # Check that the method returned the correct tweets
        assert tweets == [mock_tweet]
        
        # Check that the last processed ID was updated
        assert monitor.last_processed_id["1234567890"] == mock_tweet.id
    
    @patch("tweepy.Client")
    @patch("openai.OpenAI")
    def test_filter_security_relevant_tweets(self, mock_openai, mock_tweepy, mock_env_vars, mock_tweet):
        """Test that filter_security_relevant_tweets correctly filters tweets."""
        # Initialize the monitor
        monitor = TwitterSecurityMonitor()
        
        # Create a non-security tweet
        non_security_tweet = MagicMock()
        non_security_tweet.text = "Just released a new update to our protocol!"
        
        # Call the method with both tweets
        relevant_tweets = monitor.filter_security_relevant_tweets([mock_tweet, non_security_tweet])
        
        # Check that only the security tweet was returned
        assert len(relevant_tweets) == 1
        assert relevant_tweets[0] == mock_tweet
    
    @patch("tweepy.Client")
    @patch("openai.OpenAI")
    def test_analyze_threads(self, mock_openai, mock_tweepy, mock_env_vars, mock_tweet, mock_openai_response):
        """Test that analyze_threads correctly analyzes tweets."""
        # Set up the mock OpenAI client
        mock_openai.return_value.chat.completions.create.return_value = mock_openai_response
        
        # Initialize the monitor
        monitor = TwitterSecurityMonitor()
        
        # Call the method
        alerts = monitor.analyze_threads([mock_tweet])
        
        # Check that OpenAI was called with the correct parameters
        mock_openai.return_value.chat.completions.create.assert_called_once()
        call_args = mock_openai.return_value.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4o"
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["role"] == "user"
        assert "Tweet: " + mock_tweet.text in call_args["messages"][0]["content"]
        
        # Check that the method returned an alert
        assert len(alerts) == 1
        assert "SECURITY ALERT" in alerts[0]
        assert "Critical vulnerability in DeFi protocol XYZ" in alerts[0]
        assert "Severity: HIGH" in alerts[0]
        assert "Urgency: IMMEDIATE" in alerts[0]
        assert "Affected Systems: XYZ Protocol" in alerts[0]
    
    @patch("tweepy.Client")
    @patch("openai.OpenAI")
    def test_format_security_alert(self, mock_openai, mock_tweepy, mock_env_vars, mock_tweet):
        """Test that format_security_alert correctly formats alerts."""
        # Initialize the monitor
        monitor = TwitterSecurityMonitor()
        
        # Create threat details
        threat_details = {
            "summary": "Critical vulnerability in DeFi protocol XYZ",
            "affected_systems": ["XYZ Protocol"],
            "severity": "HIGH",
            "urgency": "IMMEDIATE"
        }
        
        # Call the method
        alert = monitor.format_security_alert(mock_tweet, threat_details)
        
        # Check that the alert contains the expected information
        assert "SECURITY ALERT: Critical vulnerability in DeFi protocol XYZ" in alert
        assert "Severity: HIGH" in alert
        assert "Urgency: IMMEDIATE" in alert
        assert "Affected Systems: XYZ Protocol" in alert
        assert f"https://twitter.com/twitter/status/{mock_tweet.id}" in alert
        assert "Original Tweet: " + mock_tweet.text in alert
    
    @patch("tweepy.Client")
    @patch("openai.OpenAI")
    def test_check_all_sources(self, mock_openai, mock_tweepy, mock_env_vars, mock_tweet, mock_openai_response):
        """Test that check_all_sources correctly checks all trusted sources."""
        # Set up the mock Twitter client
        mock_response = MagicMock()
        mock_response.data = [mock_tweet]
        mock_tweepy.return_value.get_users_tweets.return_value = mock_response
        
        # Set up the mock OpenAI client
        mock_openai.return_value.chat.completions.create.return_value = mock_openai_response
        
        # Initialize the monitor
        monitor = TwitterSecurityMonitor()
        
        # Override the trusted sources list for testing
        monitor.trusted_sources = ["1234567890", "0987654321"]
        
        # Call the method
        alerts = monitor.check_all_sources()
        
        # Check that the Twitter client was called for each trusted source
        assert mock_tweepy.return_value.get_users_tweets.call_count == 2
        
        # Check that the method returned the correct number of alerts
        assert len(alerts) == 2  # One alert for each trusted source
