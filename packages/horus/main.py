"""
Horus - Crypto Security Monitoring Agent

This is the main entry point for the Horus security monitoring agent.
"""
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Import and re-export the setup_agent function for backward compatibility
from core.agent_kit import agent_kit_manager


# Define setup_agent for backward compatibility
def setup_agent():
    """Set up all necessary components for the Horus agent (backward compatibility)."""
    return agent_kit_manager.setup_agent()


def main():
    """Main entry point for the Horus security monitoring agent."""
    try:
        from cli.app import main as cli_main
        cli_main()
    except ImportError as e:
        logger.error(f"Failed to import required modules: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
