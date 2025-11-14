"""
OpenAI-compatible chat completion models

These models match the OpenAI API format for compatibility.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message"""
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name of the participant")


class ChatCompletionRequest(BaseModel):
    """Request for chat completion (OpenAI-compatible)"""
    model: str = Field(..., description="Model to use (e.g., gpt-4, claude-3-opus)")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling")
    n: Optional[int] = Field(1, ge=1, description="Number of completions to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream responses")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    user: Optional[str] = Field(None, description="User identifier")


class ChatCompletionChoice(BaseModel):
    """A single completion choice"""
    index: int = Field(..., description="Choice index")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")


class UsageInfo(BaseModel):
    """Token usage information"""
    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")


class ChatCompletionResponse(BaseModel):
    """Response for chat completion (OpenAI-compatible)"""
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used")
    choices: List[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: Optional[UsageInfo] = Field(None, description="Token usage information")


class ErrorDetail(BaseModel):
    """Error detail"""
    message: str
    type: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: ErrorDetail


class SemanticThresholdUpdate(BaseModel):
    """Payload to adjust semantic cache similarity threshold."""
    similarity_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Semantic cache similarity threshold between 0.0 and 1.0",
    )


class SemanticSearchRequest(BaseModel):
    """Payload to preview semantic cache candidates."""
    prompt: str = Field(..., description="Prompt text to search for similar cache entries")
    model: Optional[str] = Field(None, description="Model filter for semantic cache")
    limit: int = Field(3, ge=1, le=10, description="Maximum number of candidates")


class SemanticCacheEntry(BaseModel):
    """Diagnostic representation of a semantic cache entry."""
    prompt_text: Optional[str] = None
    model: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    similarity: Optional[float] = None


class ResponsesRequest(BaseModel):
    """Subset of the OpenAI Responses API payload supported by the gateway."""

    model: str
    input: Optional[Union[str, List[str]]] = None
    messages: Optional[List[ChatMessage]] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: Optional[int] = Field(default=None, ge=1)

    def to_chat_completion(self) -> ChatCompletionRequest:
        """Convert request into the Chat Completions shape."""
        if self.messages:
            return ChatCompletionRequest(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
            )

        if self.input is None:
            raise ValueError("Either 'input' or 'messages' must be provided")

        if isinstance(self.input, str):
            segments = [self.input]
        else:
            segments = self.input

        if not segments:
            raise ValueError("Input cannot be empty")

        chat_messages = [
            ChatMessage(role="user", content=segment) for segment in segments
        ]

        return ChatCompletionRequest(
            model=self.model,
            messages=chat_messages,
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
        )


class GatewayApiKey(BaseModel):
    """Gateway-issued API key metadata."""
    key_id: str
    label: Optional[str] = None
    status: str = Field("active", pattern="^(active|disabled)$")
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class TenantSummary(BaseModel):
    """Lightweight representation of tenant configuration."""
    tenant_id: str
    display_name: Optional[str] = None
    allow_provider_keys: bool = False


# =============================================================================
# Three-Path API Models (Phase 3)
# =============================================================================


class PlaybookExecutionMetadata(BaseModel):
    """Metadata about playbook execution"""
    playbook_executed: bool = False
    steps_completed: List[str] = Field(default_factory=list)
    budget_used: float = 0.0
    quality_score: float = 0.0
    reasoning_tokens: int = 0
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    decision_log: List[Dict[str, Any]] = Field(default_factory=list)


class ResponseUsageInfo(BaseModel):
    """Extended usage information with reasoning tokens"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0


class ResponseObject(BaseModel):
    """OpenAI Responses API response object"""
    id: str = Field(..., description="Unique identifier")
    object: str = Field("response", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used")
    output: Dict[str, Any] = Field(..., description="Response output")
    usage: ResponseUsageInfo = Field(..., description="Token usage")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class IntentRequest(BaseModel):
    """Request for intent-based execution"""
    input: str = Field(..., description="User input to resolve")
    model: Optional[str] = Field(None, description="Model to use")
    context: Dict[str, Any] = Field(default_factory=dict)
    budget_max: float = Field(1.0, description="Maximum budget in USD")
    max_steps: int = Field(10, description="Maximum execution steps")


class Intent(BaseModel):
    """Resolved intent"""
    id: str = Field(..., description="Intent identifier")
    name: str = Field(..., description="Intent name")
    confidence: float = Field(..., description="Confidence score")
    embedding: List[float] = Field(default_factory=list)


class IntentResponse(BaseModel):
    """Response for intent-based execution"""
    intent: str = Field(..., description="Resolved intent name")
    confidence: float = Field(..., description="Intent confidence")
    playbook_id: str = Field(..., description="Playbook identifier")
    artifacts: List[Dict[str, Any]] = Field(..., description="Execution artifacts")
    cost: float = Field(..., description="Total cost in USD")
    execution_log: List[str] = Field(..., description="Execution log")
    rate_limit_per_minute: Optional[int] = Field(None, ge=0)


class PlaybookExecuteRequest(BaseModel):
    """Request to execute a playbook with Re^Re Loop"""
    intent: str = Field(..., description="User intent/request to execute")
    max_steps: int = Field(10, ge=1, le=50, description="Maximum number of steps")
    budget_max: float = Field(1.0, ge=0.01, le=100.0, description="Maximum budget in USD")
    model: str = Field("gpt-4o", description="Model to use for execution")
