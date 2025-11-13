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
