from fastapi import APIRouter, Depends, HTTPException
from database import session
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Annotated, List, Optional
from starlette import status
from models import Status, User, Friends
from pydantic import BaseModel, validator
from datetime import datetime

router = APIRouter(
    prefix='/status',
    tags=['status']

)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class TextStatus(BaseModel):
    text: str
    color: str

@router.post("/text", status_code=status.HTTP_201_CREATED)
async def upload_text_status(db: db_dependency, phone_number: str, status: TextStatus):
    user=db.query(User).filter(phone_number == User.phone_number).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user is not found')
    try:
        newStatus=Status(
            user_id=user.id, 
            status_text=status.text,
            status_type='text',
            status_text_color=status.color
        )
        db.add(newStatus)
        db.commit()
    except Exception as e:
        raise e


class mediaStatus(BaseModel):
    media_link: str

@router.post("/media", status_code=status.HTTP_201_CREATED)
async def upload_media_status(db: db_dependency, phone_number: str, status: mediaStatus):
    user=db.query(User).filter(phone_number == User.phone_number).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user is not found')
    try:
        print(status.media_link)
        newStatus=Status(
            user_id=user.id, 
            status_link=status.media_link,
            status_type='media'
        )
        db.add(newStatus)
        db.commit()
    except Exception as e:
        print(str(e))
        raise e

 
class StatusResponse(BaseModel):
    media_link: Optional[str] = None
    text: Optional[str] = None
    status_type: str
    uploaded_at: str
    color: str

    @validator('uploaded_at')
    def validate_uploaded_at(cls, value):
        try:
            
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError('uploaded_at must be a valid ISO 8601 datetime string')
        return value

class UserFriendStatus(BaseModel):
    name: str
    profile_picture: str
    uploaded_at: str
    phone_number: str
    status: List[StatusResponse]

    @validator('uploaded_at')
    def validate_uploaded_at(cls, value):
        try:
            
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError('uploaded_at must be a valid ISO 8601 datetime string')
        return value

@router.get('/', status_code=status.HTTP_200_OK, response_model=List[UserFriendStatus])
async def get_friend_status(db: db_dependency, phone_number: str):
    try:
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
        friends = db.query(Friends).filter(or_(Friends.friend1 == user.id, Friends.friend2 == user.id)).all()
        friend_ids = [x.friend1 if x.friend1 != user.id else x.friend2 for x in friends]
        response_chats = []
        for friend_id in friend_ids:
            statuses = db.query(Status).filter(Status.user_id == friend_id).all()
            friend_status = [
                StatusResponse(
                    media_link=s.status_link if s.status_type == 'media' else None,
                    text=s.status_text if s.status_type == 'text' else None,
                    status_type=s.status_type,
                    uploaded_at=s.uploaded_at if isinstance(s.uploaded_at, str) else s.uploaded_at.isoformat(),
                    color=str(s.status_text_color)
                ) for s in statuses
            ]
            friend_status.sort(key=lambda x: x.uploaded_at, reverse=False)
            if len(friend_status) == 0:
                continue
            friend_details = db.query(User).filter(User.id == friend_id).first()
            if friend_details:
                response_chats.append(
                    UserFriendStatus(
                        name=friend_details.name,
                        profile_picture=friend_details.profile_picture,
                        uploaded_at=friend_status[-1].uploaded_at if friend_status else '',
                        status=friend_status,
                        phone_number=friend_details.phone_number
                    )
                )
        response_chats.sort(key=lambda x: x.uploaded_at, reverse=True)
        return response_chats
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get('/my', status_code=status.HTTP_200_OK, response_model=List[StatusResponse])
async def get_my_status(db: db_dependency, phone_number: str):
    try:
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
        statuses = db.query(Status).filter(user.id == Status.user_id).all()
        response_chats = [
            StatusResponse(
                media_link=status.status_link,
                text=status.status_text,
                color=str(status.status_text_color),
                status_type=status.status_type,
                uploaded_at=status.uploaded_at if isinstance(status.uploaded_at, str) else status.uploaded_at.isoformat(),
            ) for status in statuses
        ]
        response_chats.sort(key=lambda x: x.uploaded_at)
        return response_chats
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")













