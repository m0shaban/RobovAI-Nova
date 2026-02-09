from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


class BaseTool(ABC):
    """
    Abstract Base Class for all RobovAI tools.
    """

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.context = context or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool (e.g., '/social', '/imagine')."""
        pass

    @property
    def args_schema(self) -> Optional[Type[BaseModel]]:
        """Optional Pydantic model for tool arguments. If None, defaults to single 'query' string."""
        return None

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what the tool does."""
        pass

    @property
    @abstractmethod
    def cost(self) -> int:
        """Token cost per execution."""
        pass

    @abstractmethod
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        Main execution logic.
        :param user_input: The raw text argument provided by the user.
        :param user_id: ID of the user invoking the tool (for logging/personalization).
        :return: A dictionary containing the result, status, and any metadata.
        """
        pass

    def validate_balance(self, current_balance: int) -> bool:
        """Checks if user has enough tokens."""
        return current_balance >= self.cost
