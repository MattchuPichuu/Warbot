"""Data models for timer management system."""
from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone, timedelta
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
    timer_type: Literal["friendly_hit", "enemy_hit", "pro_whack"] = Field(
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
    timer_type: Optional[Literal["friendly_hit", "enemy_hit", "pro_whack"]] = None
    time_shot: Optional[datetime] = None

    @validator('user_name')
    def validate_user_name(cls, v):
        """Validate and sanitize user_name field if provided."""
        if v is not None and not v.strip():
            raise ValueError('user_name cannot be empty or whitespace')
        return v.strip() if v else v


class TimerResponse(BaseModel):
    """Pydantic model for timer response data with calculated Pro Drop windows."""

    id: int
    user_name: str
    timer_type: str
    time_shot: datetime
    pro_drop_start: Optional[datetime] = None
    pro_drop_end: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True

    @validator('pro_drop_start', always=True, pre=False)
    def calculate_pro_drop_start(cls, v, values):
        """Calculate Pro Drop Start based on timer_type and time_shot."""
        if 'timer_type' not in values or 'time_shot' not in values:
            return None

        timer_type = values['timer_type']
        time_shot = values['time_shot']

        if timer_type == 'friendly_hit':
            # Friendly Hit: Pro Drop Start = Time + 3h 40m
            return time_shot + timedelta(hours=3, minutes=40)
        elif timer_type == 'enemy_hit':
            # Enemy Hit: Pro Drop Start = Time + 3h 40m
            return time_shot + timedelta(hours=3, minutes=40)
        elif timer_type == 'pro_whack':
            # Pro Whack: Pro Drop = Time + 15m
            return time_shot + timedelta(minutes=15)

        return None

    @validator('pro_drop_end', always=True, pre=False)
    def calculate_pro_drop_end(cls, v, values):
        """Calculate Pro Drop End based on timer_type and time_shot."""
        if 'timer_type' not in values or 'time_shot' not in values:
            return None

        timer_type = values['timer_type']
        time_shot = values['time_shot']

        if timer_type == 'friendly_hit' or timer_type == 'enemy_hit':
            # Both Friendly Hit and Enemy Hit: Pro Drop End = Time + 4h 20m
            return time_shot + timedelta(hours=4, minutes=20)
        elif timer_type == 'pro_whack':
            # Pro Whack: Single time, end = start (15 min)
            return time_shot + timedelta(minutes=15)

        return None
