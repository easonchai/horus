"""
Base functionality for Horus security tools.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, TypeVar

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Type for tool functions
T = TypeVar('T')
ToolFunction = Callable[[Dict[str, Any]], str]


class BaseTool(ABC):
    """
    Abstract base class for all Horus security tools.
    """
    
    def __init__(self, name: str):
        """
        Initialize the tool with a name.
        
        Args:
            name: The name of the tool.
        """
        self.name = name
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute the tool with the given parameters.
        
        Args:
            parameters: Dictionary containing parameters for the tool.
            
        Returns:
            A string describing the action taken.
        """
        pass
    
    def __call__(self, parameters: Dict[str, Any]) -> str:
        """
        Make the tool callable directly.
        
        Args:
            parameters: Dictionary containing parameters for the tool.
            
        Returns:
            A string describing the action taken.
        """
        return self.execute(parameters)


def create_tool(name: str, execute_fn: Callable[[Dict[str, Any]], str]) -> ToolFunction:
    """
    Create a tool function with the given name and execution function.
    
    Args:
        name: The name of the tool.
        execute_fn: The function that implements the tool's functionality.
        
    Returns:
        A tool function that can be called with parameters.
    """
    def tool_function(parameters: Dict[str, Any]) -> str:
        """
        Execute the tool with the given parameters.
        
        Args:
            parameters: Dictionary containing parameters for the tool.
            
        Returns:
            A string describing the action taken.
        """
        return execute_fn(parameters)
    
    # Add metadata to the function
    tool_function.__name__ = name
    tool_function.__doc__ = execute_fn.__doc__
    
    return tool_function
