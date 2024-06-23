from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from database import session

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix='/chat',
    tags=['Chat']
)