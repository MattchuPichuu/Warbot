"""FastAPI backend for War Bot timer management system."""
from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import models
import database
from auth import get_api_key
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="War Timer API", version="1.0.0")

# Dependency
def get_db():
    """
    Database session dependency for FastAPI endpoints.

    Yields:
        Session: SQLAlchemy database session

    Note:
        Automatically closes the session after request completion
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/timers/", response_model=models.TimerResponse)
def create_timer(
    timer: models.TimerCreate,
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """
    Create a new timer entry.

    Args:
        timer: Timer data to create
        db: Database session
        api_key: API key for authentication

    Returns:
        TimerResponse: Created timer with ID

    Raises:
        HTTPException: If database error occurs
    """
    try:
        logger.info(f"Creating timer for user {timer.user_name}, type: {timer.timer_type}")
        db_timer = models.Timer(**timer.dict())
        db.add(db_timer)
        db.commit()
        db.refresh(db_timer)
        logger.info(f"Timer created successfully with ID {db_timer.id}")
        return db_timer
    except SQLAlchemyError as e:
        logger.error(f"Database error creating timer: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while creating timer"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating timer: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@app.get("/timers/", response_model=List[models.TimerResponse])
def read_timers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """
    Retrieve a list of timers.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return (max 500)
        db: Database session
        api_key: API key for authentication

    Returns:
        List[TimerResponse]: List of timer records

    Raises:
        HTTPException: If database error occurs
    """
    try:
        # Cap the limit at 500 to prevent excessive queries
        limit = min(limit, 500)
        logger.info(f"Fetching timers with skip={skip}, limit={limit}")
        timers = db.query(models.Timer).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(timers)} timers")
        return timers
    except SQLAlchemyError as e:
        logger.error(f"Database error reading timers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while reading timers"
        )
    except Exception as e:
        logger.error(f"Unexpected error reading timers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@app.get("/timers/{timer_id}", response_model=models.TimerResponse)
def get_timer(
    timer_id: int,
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """
    Retrieve a specific timer by ID.

    Args:
        timer_id: ID of the timer to retrieve
        db: Database session
        api_key: API key for authentication

    Returns:
        TimerResponse: The requested timer

    Raises:
        HTTPException: If timer not found or database error
    """
    try:
        logger.info(f"Fetching timer with ID {timer_id}")
        timer = db.query(models.Timer).filter(models.Timer.id == timer_id).first()
        if timer is None:
            logger.warning(f"Timer with ID {timer_id} not found")
            raise HTTPException(status_code=404, detail="Timer not found")
        return timer
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error reading timer {timer_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while reading timer"
        )
    except Exception as e:
        logger.error(f"Unexpected error reading timer {timer_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@app.put("/timers/{timer_id}", response_model=models.TimerResponse)
def update_timer(
    timer_id: int,
    timer_update: models.TimerUpdate,
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """
    Update an existing timer.

    Args:
        timer_id: ID of the timer to update
        timer_update: Fields to update
        db: Database session
        api_key: API key for authentication

    Returns:
        TimerResponse: Updated timer

    Raises:
        HTTPException: If timer not found or database error
    """
    try:
        logger.info(f"Updating timer with ID {timer_id}")
        timer = db.query(models.Timer).filter(models.Timer.id == timer_id).first()
        if timer is None:
            logger.warning(f"Timer with ID {timer_id} not found")
            raise HTTPException(status_code=404, detail="Timer not found")

        # Update only provided fields
        update_data = timer_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(timer, field, value)

        db.commit()
        db.refresh(timer)
        logger.info(f"Timer {timer_id} updated successfully")
        return timer
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating timer {timer_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while updating timer"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating timer {timer_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@app.delete("/timers/{timer_id}")
def delete_timer(
    timer_id: int,
    db: Session = Depends(get_db),
    api_key: str = Security(get_api_key)
):
    """
    Delete a timer by ID.

    Args:
        timer_id: ID of the timer to delete
        db: Database session
        api_key: API key for authentication

    Returns:
        dict: Success message

    Raises:
        HTTPException: If timer not found or database error
    """
    try:
        logger.info(f"Deleting timer with ID {timer_id}")
        timer = db.query(models.Timer).filter(models.Timer.id == timer_id).first()
        if timer is None:
            logger.warning(f"Timer with ID {timer_id} not found")
            raise HTTPException(status_code=404, detail="Timer not found")

        db.delete(timer)
        db.commit()
        logger.info(f"Timer {timer_id} deleted successfully")
        return {"message": f"Timer {timer_id} deleted successfully"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting timer {timer_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while deleting timer"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting timer {timer_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )
