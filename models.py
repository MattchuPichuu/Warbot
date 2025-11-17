"""Data models for timer management system."""
from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone
from database import Base
from typing import Literal, Optional

class Timer(Base):
    """SQLAlchemy model for timer entries."""

    __tablename__ = "timers"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    timer_type = Column(String, index=True)
    time_shot = Column(DateTime)

class TimerCreate(BaseModel):
    """Pydantic model for creating a new timer entry."""

    user_name: str = Field(..., min_length=1, max_length=100)
    timer_type: Literal["friendly_hit", "enemy_hit", "defensive_hit"] = Field(
        ..., description="Type of timer event"
    )
    time_shot: datetime

    @validator('user_name')
    def validate_user_name(cls, v):
        """Validate and sanitize user_name field."""
        if not v.strip():
            raise ValueError('user_name cannot be empty or whitespace')
        return v.strip()

class TimerUpdate(BaseModel):
    """Pydantic model for updating an existing timer entry."""

    user_name: Optional[str] = Field(None, min_length=1, max_length=100)
    timer_type: Optional[Literal["friendly_hit", "enemy_hit", "defensive_hit"]] = None
    time_shot: Optional[datetime] = None

    @validator('user_name')
    def validate_user_name(cls, v):
        """Validate and sanitize user_name field if provided."""
        if v is not None and not v.strip():
            raise ValueError('user_name cannot be empty or whitespace')
        return v.strip() if v else v


class TimerResponse(BaseModel):
    """Pydantic model for timer response data."""

    id: int
    user_name: str
    timer_type: str
    time_shot: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True
