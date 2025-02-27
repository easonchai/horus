#!/usr/bin/env python3
"""
Unit tests for the MonitorTool class in the Horus security system.

This test suite provides comprehensive testing for the MonitorTool class,
covering its initialization, subscriber management, monitoring configuration
and execution of monitoring operations.
"""
import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the MonitorTool class and create_monitor_tool function
from horus.tools.monitor import MonitorTool, create_monitor_tool


class TestMonitorTool(unittest.TestCase):
    """Test cases for the MonitorTool class."""

    def setUp(self):
        """Set up test fixtures before each test."""
        self.default_tool = MonitorTool()
        self.subscribers = ["0x1234567890123456789012345678901234567890", "email@example.com"]
        self.custom_tool = MonitorTool(self.subscribers)
    
    def test_init(self):
        """Test initialization of MonitorTool."""
        # Test default initialization
        self.assertEqual(self.default_tool.name, "monitor")
        self.assertEqual(self.default_tool.alert_subscribers, [])
        self.assertEqual(self.default_tool.active_monitors, {})
        
        # Test initialization with subscribers
        self.assertEqual(self.custom_tool.name, "monitor")
        self.assertEqual(self.custom_tool.alert_subscribers, self.subscribers)
        self.assertEqual(self.custom_tool.active_monitors, {})
    
    def test_add_subscriber(self):
        """Test adding subscribers to MonitorTool."""
        # Add a subscriber to the default tool
        subscriber = "new_subscriber@example.com"
        self.default_tool.add_subscriber(subscriber)
        self.assertIn(subscriber, self.default_tool.alert_subscribers)
        
        # Add a duplicate subscriber
        self.default_tool.add_subscriber(subscriber)
        # Should only appear once
        self.assertEqual(self.default_tool.alert_subscribers.count(subscriber), 1)
    
    def test_remove_subscriber(self):
        """Test removing subscribers from MonitorTool."""
        # Remove a subscriber from the custom tool
        subscriber = self.subscribers[0]
        self.custom_tool.remove_subscriber(subscriber)
        self.assertNotIn(subscriber, self.custom_tool.alert_subscribers)
        
        # Remove a non-existent subscriber - should not raise an error
        self.custom_tool.remove_subscriber("nonexistent")
    
    def test_get_active_monitors(self):
        """Test retrieving active monitors."""
        # Add some test monitors
        self.default_tool.active_monitors = {
            "ETH:1": {"asset": "ETH", "chain_id": "1", "duration": "24h"},
            "USDC:1": {"asset": "USDC", "chain_id": "1", "duration": "48h"},
            "BTC:84532": {"asset": "BTC", "chain_id": "84532", "duration": "12h"}
        }
        
        # Get all monitors
        all_monitors = self.default_tool.get_active_monitors()
        self.assertEqual(len(all_monitors), 3)
        
        # Get monitors filtered by chain
        chain_monitors = self.default_tool.get_active_monitors("1")
        self.assertEqual(len(chain_monitors), 2)
        self.assertIn("ETH:1", chain_monitors)
        self.assertIn("USDC:1", chain_monitors)
        
        # Get monitors for a chain with only one monitor
        base_monitors = self.default_tool.get_active_monitors("84532")
        self.assertEqual(len(base_monitors), 1)
        self.assertIn("BTC:84532", base_monitors)
        
        # Get monitors for a chain with no monitors
        empty_monitors = self.default_tool.get_active_monitors("137")
        self.assertEqual(len(empty_monitors), 0)
    
    def test_execute_basic(self):
        """Test basic execution of the monitor tool."""
        # Execute with minimal parameters
        result = self.default_tool.execute({"asset": "ETH"})
        
        # Check that the result contains expected information
        self.assertIn("Enhanced monitoring activated for ETH", result)
        self.assertIn("for the next 24h", result)
        self.assertIn("5%", result)
        
        # Check that a monitor was added to active_monitors
        self.assertEqual(len(self.default_tool.active_monitors), 1)
        self.assertIn("ETH:84532", self.default_tool.active_monitors)
    
    def test_execute_with_custom_parameters(self):
        """Test execution with custom parameters."""
        # Execute with custom parameters
        params = {
            "asset": "USDC",
            "duration": "72h",
            "threshold": "10%",
            "chain_id": "1",
            "alert_type": "volume"
        }
        result = self.custom_tool.execute(params)
        
        # Check that the result contains expected information
        self.assertIn("Enhanced monitoring activated for USDC", result)
        self.assertIn("for the next 72h", result)
        self.assertIn("10%", result)
        self.assertIn("volume movements", result)
        self.assertIn("chain 1", result)
        
        # Check that subscribers are mentioned
        self.assertIn("2 configured recipients", result)
        
        # Check that a monitor was added to active_monitors
        self.assertEqual(len(self.custom_tool.active_monitors), 1)
        self.assertIn("USDC:1", self.custom_tool.active_monitors)
        
        # Check the monitor configuration
        monitor = self.custom_tool.active_monitors["USDC:1"]
        self.assertEqual(monitor["asset"], "USDC")
        self.assertEqual(monitor["duration"], "72h")
        self.assertEqual(monitor["threshold"], "10%")
        self.assertEqual(monitor["chain_id"], "1")
        self.assertEqual(monitor["alert_type"], "volume")
        self.assertTrue(monitor["active"])
        self.assertEqual(monitor["subscribers"], self.subscribers)
    
    def test_execute_with_additional_subscribers(self):
        """Test execution with additional subscribers."""
        # Execute with additional subscribers
        new_subscriber = "new_subscriber@example.com"
        params = {
            "asset": "ETH",
            "notify": [new_subscriber]
        }
        result = self.default_tool.execute(params)
        
        # Check that the new subscriber was added
        self.assertIn(new_subscriber, self.default_tool.alert_subscribers)
        
        # Check that the monitor configuration includes the new subscriber
        monitor = self.default_tool.active_monitors["ETH:84532"]
        self.assertIn(new_subscriber, monitor["subscribers"])
    
    def test_factory_function(self):
        """Test the create_monitor_tool factory function."""
        # Create a tool with the factory function
        tool = create_monitor_tool()
        self.assertIsInstance(tool, MonitorTool)
        self.assertEqual(tool.alert_subscribers, [])
        
        # Create a tool with subscribers
        subscribers = ["0x1234", "test@example.com"]
        tool_with_subscribers = create_monitor_tool(subscribers)
        self.assertIsInstance(tool_with_subscribers, MonitorTool)
        self.assertEqual(tool_with_subscribers.alert_subscribers, subscribers)
    
    def test_callable_interface(self):
        """Test that the MonitorTool instance is callable."""
        # The __call__ method is inherited from BaseTool
        result = self.default_tool({"asset": "BTC", "duration": "12h"})
        
        # Check that the result contains expected information
        self.assertIn("Enhanced monitoring activated for BTC", result)
        self.assertIn("for the next 12h", result)
        
        # Check that a monitor was added to active_monitors
        self.assertIn("BTC:84532", self.default_tool.active_monitors)


if __name__ == "__main__":
    unittest.main() 