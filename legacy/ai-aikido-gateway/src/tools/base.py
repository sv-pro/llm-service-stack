"""
Base classes for tools in the playbook system.

Provides the Tool abstract base class and ToolResult data class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result returned by tool execution"""

    success: bool = True
    data: Dict[str, Any]
    cost: float = 0.0
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found in registry"""

    pass


class Tool(ABC):
    """
    Abstract base class for all tools.

    Tools are executable units that can be invoked by the playbook workflow.
    Each tool must implement the execute() method.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a tool.

        Args:
            name: Unique tool identifier
            description: Human-readable description
            input_schema: JSON schema for input validation (optional)
            output_schema: JSON schema for output validation (optional)
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given input.

        Args:
            input_data: Input parameters for tool execution

        Returns:
            ToolResult with execution output

        Raises:
            Exception: If tool execution fails
        """
        pass

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input against schema.

        Args:
            data: Input data to validate

        Note: For Phase 3 prototype, validation is optional.
        Full implementation would use jsonschema library.
        """
        # TODO: Implement JSON schema validation
        pass

    def validate_output(self, data: Dict[str, Any]) -> None:
        """
        Validate output against schema.

        Args:
            data: Output data to validate

        Note: For Phase 3 prototype, validation is optional.
        Full implementation would use jsonschema library.
        """
        # TODO: Implement JSON schema validation
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool to dictionary representation.

        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }
