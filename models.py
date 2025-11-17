from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel
from datetime import datetime
from database import Base

class Timer(Base):
    __tablename__ = "timers"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    timer_type = Column(String, index=True)
    time_shot = Column(DateTime)

class TimerCreate(BaseModel):
    user_name: str
    timer_type: str
    time_shot: datetime

class TimerResponse(BaseModel):
    id: int
    user_name: str
    timer_type: str
    time_shot: datetime

    class Config:
        orm_mode = True
