"""Database models for usage logs and tracking."""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime

from .database import Base


class UsageLog(Base):
    """Model for tracking LLM usage and costs."""
    
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    model = Column(String, index=True)
    provider = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(Float)
    latency_ms = Column(Float)
    user_id = Column(String, index=True, nullable=True)
    api_key_id = Column(String, index=True, nullable=True)
    request_data = Column(JSON)
    response_data = Column(JSON)
    cache_hit = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, model={self.model}, tokens={self.total_tokens}, cost={self.cost})>"


class CostTracking(Base):
    """Model for aggregated cost tracking."""

    __tablename__ = "cost_tracking"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    model = Column(String, index=True)
    total_requests = Column(Integer)
    total_tokens = Column(Integer)
    total_cost = Column(Float)
    user_id = Column(String, index=True, nullable=True)


class EnhancedPrompt(Base):
    """Model for storing enhanced prompts (Stage 2: Smart Prompts)."""

    __tablename__ = "enhanced_prompts"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Original prompt
    original_system = Column(String)
    original_user = Column(String)

    # Enhanced prompt
    enhanced_system = Column(String)
    enhanced_user = Column(String)

    # Metadata
    improvements = Column(JSON)  # List of improvements made
    detected_intent = Column(String, index=True)
    reasoning = Column(String)
    confidence = Column(Float)

    # Which model was used for enhancement
    model_used = Column(String)

    # User feedback (tracks what users do with enhanced prompts)
    user_feedback = Column(String, nullable=True)  # 'used' | 'edited' | 'discarded'
    feedback_timestamp = Column(DateTime, nullable=True)

    # Experimental: Recursive enhancement metadata
    recursive_iterations = Column(Integer, nullable=True)  # Number of iterations performed
    recursive_converged = Column(Integer, nullable=True)  # 1 if converged, 0 if hit max iterations
    recursive_final_similarity = Column(Float, nullable=True)  # Final similarity score
    recursive_history = Column(JSON, nullable=True)  # Full iteration history

    def __repr__(self):
        return f"<EnhancedPrompt(id={self.id}, intent={self.detected_intent}, confidence={self.confidence})>"
