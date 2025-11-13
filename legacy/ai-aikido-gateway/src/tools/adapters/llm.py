"""
LLM tool adapter for calling language models as tools.

Integrates with the existing LiteLLM infrastructure.
"""

from typing import Dict, Any
import litellm
from ..base import Tool, ToolResult


class LLMTool(Tool):
    """
    Tool adapter for calling LLMs.

    Uses LiteLLM to support multiple providers (OpenAI, Anthropic, etc.).
    """

    def __init__(
        self,
        model: str,
        name: str = None,
        description: str = None,
        temperature: float = 1.0,
        max_tokens: int = None,
    ):
        """
        Initialize LLM tool.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
            name: Tool name (defaults to "llm_{model}")
            description: Tool description (defaults to "Call {model} LLM")
            temperature: Sampling temperature (default: 1.0)
            max_tokens: Maximum tokens to generate (optional)
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        tool_name = name or f"llm_{model.replace('/', '_').replace('-', '_')}"
        tool_description = description or f"Call {model} LLM"

        super().__init__(
            name=tool_name,
            description=tool_description,
            input_schema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "Array of message objects",
                    },
                    "temperature": {"type": "number", "description": "Temperature"},
                    "max_tokens": {
                        "type": "integer",
                        "description": "Max tokens to generate",
                    },
                },
                "required": ["messages"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "model": {"type": "string"},
                    "usage": {"type": "object"},
                },
            },
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute LLM call.

        Args:
            input_data: Dictionary with:
                - messages: List of message dictionaries
                - temperature: Optional temperature override
                - max_tokens: Optional max_tokens override

        Returns:
            ToolResult with LLM response
        """
        messages = input_data.get("messages", [])
        temperature = input_data.get("temperature", self.temperature)
        max_tokens = input_data.get("max_tokens", self.max_tokens)

        try:
            # Call LiteLLM
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response content
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            # Calculate cost (litellm provides this)
            cost = litellm.completion_cost(completion_response=response)

            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "model": response.model,
                    "usage": usage,
                },
                cost=cost,
                metadata={
                    "model": self.model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                metadata={
                    "model": self.model,
                    "exception_type": type(e).__name__,
                },
            )
