"""
Base class for all tools in the Horus system.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all tools."""
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute the tool with the given parameters.
        
        Args:
            parameters: The parameters for the tool execution.
            
        Returns:
            A string describing the result of the execution.
        """
        pass
