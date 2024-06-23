from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from typing import Annotated
from database import session
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Media, User, Friends, NotificationToken
from sqlalchemy import or_ ,and_ 
from routers.firebase_notifications import send_message_notificaiton

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix='/message',
    tags=['message']
)

db_dependency = Annotated[Session, Depends(get_db)]

class ImageRequest(BaseModel):
    image: str
    phoneNumber: str
    
@router.post("/send_image", status_code=status.HTTP_201_CREATED)
async def send_image(
    db: Annotated[Session, Depends(get_db)], 
    image: ImageRequest, 
    phone_number: str
):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    friend = db.query(User).filter(User.phone_number == image.phoneNumber).first()
    if user is None or friend is None:
        raise HTTPException(status_code=404, detail='User not found')

    user_id = user.id
    friend_id = friend.id
    
    try:
        ImageFile = Media(
            sender=user_id,
            receiver=friend_id,
            media_link=image.image,
            media_type='image'
        )
        db.add(ImageFile)
        db.commit()
        print("Image sent")

        db.query(Friends).filter(
            or_(
                and_(Friends.friend1 == user_id, Friends.friend2 == friend_id),
                and_(Friends.friend1 == friend_id, Friends.friend2 == user_id)
            )
        ).update({
            Friends.last_message: 'Image',
            Friends.last_message_time: ImageFile.sent_at,
            Friends.last_message_type: 'image'
        })
        db.commit()
        token = db.query(NotificationToken).filter(friend_id == NotificationToken.user_id).first()
        send_message_notificaiton(token.token, user.name, 'You have a new image', image.image)
        print("Updated last message")
        return {
            'message': 'Image sent'
        }
    except Exception as e:
        db.rollback()  # Rollback transaction in case of error
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail='Image not sent')