from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/timers/", response_model=models.TimerResponse)
def create_timer(timer: models.TimerCreate, db: Session = Depends(get_db)):
    db_timer = models.Timer(**timer.dict())
    db.add(db_timer)
    db.commit()
    db.refresh(db_timer)
    return db_timer

@app.get("/timers/", response_model=List[models.TimerResponse])
def read_timers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    timers = db.query(models.Timer).offset(skip).limit(limit).all()
    return timers
