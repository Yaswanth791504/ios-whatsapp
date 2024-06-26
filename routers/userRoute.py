from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional, List
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from models import User, Message, Friends, NotificationToken, Media
from pydantic import BaseModel, EmailStr
from datetime import datetime
from starlette import status
from database import session
from fastapi.responses import JSONResponse
from routers.firebase_notifications import send_message_notificaiton

router = APIRouter(
    prefix='/user',
    tags=['User']
)

def get_Session():
    db = session()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_Session)]

class UserRegister(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone_number: str
    about: str
    profile_picture: str
    token: str
    
class UserRegisterResponse(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone_number: str
    about: str
    profile_picture: str
    created_at: str

@router.post('/register', status_code=status.HTTP_201_CREATED, response_model=UserRegisterResponse)
async def register_user(db: db_dependency, user_request: UserRegister):
    existing_user = db.query(User).filter(User.phone_number == user_request.phone_number).first()
    if existing_user:
        notiification_token = db.query(NotificationToken).filter(NotificationToken.user_id == existing_user.id).first()
        if notiification_token:
            notiification_token.token = user_request.token
            db.commit()
            print('token updated successfully')
        raise HTTPException(status_code=404, detail='User already exists')
    else: 
        print(user_request.token)
        try:
            new_user = User(
                name=user_request.name,
                email=user_request.email,
                phone_number=user_request.phone_number,
                about=user_request.about,
                profile_picture=user_request.profile_picture,
            )
            db.add(new_user)
            db.commit() 
            token = NotificationToken(user_id=new_user.id, token=user_request.token)
            db.add(token)
            db.commit()
            
            response_user = UserRegisterResponse(
                name=new_user.name,
                email=new_user.email,
                phone_number=new_user.phone_number,
                about=new_user.about,
                profile_picture=new_user.profile_picture,
                created_at=new_user.created_at.isoformat() if isinstance(new_user.created_at, datetime) else str(new_user.created_at)
            )
            return response_user
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail={"detail": str(e)})

class UserUpdate(BaseModel):
    name: Optional[str] = None
    about: Optional[str] = None
    profile_picture: Optional[str] = None
    phone_number: str

class UserUpdateResponse(BaseModel):
    name: Optional[str]
    about: Optional[str]
    profile_picture: Optional[str]
    updated_at: str

@router.put('/update', status_code=status.HTTP_202_ACCEPTED, response_model=UserUpdateResponse)
async def update_user(db: db_dependency, user_request: UserUpdate):
    try:
        user = db.query(User).filter(User.phone_number == user_request.phone_number).first()
        if user is None:
            raise Exception('User not found')
        if user_request.name is not None:
            user.name = user_request.name
        if user_request.about is not None:
            user.about = user_request.about
        if user_request.profile_picture is not None:
            user.profile_picture = user_request.profile_picture
        user.updated_at = datetime.now()
        db.commit()
        return UserUpdateResponse(
            name=user.name,
            about=user.about,
            profile_picture=user.profile_picture,
            updated_at=user.updated_at.isoformat()
        )
    except Exception as e:
        db.rollback()
        raise e
    

class UserRequestResponse(BaseModel):
    name: str
    email: str
    phone_number : str
    about : str
    profile_picture : str
    status: bool
    token: str
    
@router.get('/get', status_code=status.HTTP_200_OK, response_model=UserRequestResponse)
async def get_user_details(db: db_dependency, phone_number: str):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        # logging.info(f'User with phone number {phone_number} not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    
    token = db.query(NotificationToken).filter(NotificationToken.user_id == user.id).first()
    
    return UserRequestResponse(
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        about=user.about,
        profile_picture=user.profile_picture,
        status=user.status,
        token=token.token
    )


class UserChatResponse(BaseModel):
    name: str
    phone_number: str
    about: str
    profile_picture : str
    last_message : str
    last_message_time : str
    last_message_type: str

@router.get('/chats', status_code=status.HTTP_200_OK, response_model=List[UserChatResponse])
async def get_user_chats(db: db_dependency, phone_number: str):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    user_id = user.id
    try:
        friends_query = db.query(Friends).filter(or_(user_id == Friends.friend1, user_id == Friends.friend2))
        friends = friends_query.all()
        friend_ids = [f.friend1 if f.friend1 != user_id else f.friend2 for f in friends]
        response_chats = []
        for friend_id in friend_ids:
            friend_user = db.query(User).filter(User.id == friend_id).first()
            if not friend_user:
                continue 
            last_message = db.query(Friends).filter(
                or_(
                    and_(Friends.friend1 == user_id, Friends.friend2 == friend_id),
                    and_(Friends.friend1 == friend_id, Friends.friend2 == user_id)
                )
            ).first()
            if not last_message:
                continue 
            response_chats.append(
                UserChatResponse(
                    name=friend_user.name,
                    last_message=last_message.last_message,
                    last_message_time=last_message.last_message_time.isoformat(),
                    phone_number=friend_user.phone_number,
                    about=friend_user.about,
                    profile_picture=friend_user.profile_picture,
                    last_message_type=last_message.last_message_type
                )
            )

            response_chats.sort(key=lambda x: x.last_message_time, reverse=True)
            print(response_chats)
        return response_chats
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

class Messages(BaseModel):
    message: str
    message_time: str
    sender: bool
    message_type: Optional[str] = None

@router.get('/messages', status_code=status.HTTP_200_OK, response_model=List[Messages])
async def get_messages(db: db_dependency, user_phone_number: str, friend_phone_number: str):
    user = db.query(User).filter(User.phone_number == user_phone_number).first()
    friend = db.query(User).filter(User.phone_number == friend_phone_number).first()
    if user is None or friend is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    user_id = user.id
    friend_id = friend.id
    try:
        text_messages = db.query(Message).filter(
            or_(
                and_(Message.receiver == user_id, Message.sender == friend_id),
                and_(Message.receiver == friend_id, Message.sender == user_id)
            )
        ).all()
        image_messages = db.query(Media).filter(
            or_(
                and_(Media.receiver == user_id, Media.sender == friend_id),
                and_(Media.receiver == friend_id, Media.sender == user_id)
            )
        ).all()
        response_messages = []
        for message in text_messages:
            response_messages.append(
                Messages(
                    message=message.message,
                    message_time=message.sent_at.isoformat(),
                    sender=True if message.sender == user_id else False,
                    message_type='text'
                )
            )
        for message in image_messages:
            response_messages.append(
                Messages(
                    message=message.media_link,
                    message_time=message.sent_at.isoformat(),
                    sender=True if message.sender == user_id else False,
                    message_type='image'
                )
            )
        response_messages.sort(key=lambda x: x.message_time)
        return response_messages
    except Exception as e:
        raise e


class UserMessage(BaseModel):
    message: str
    friend_phone_number: str
@router.post('/message', status_code=status.HTTP_201_CREATED)
async def update_user_message(user_phone_number: str, message: UserMessage, db: db_dependency):
    try:
        user = db.query(User).filter(User.phone_number == user_phone_number).first()
        friend = db.query(User).filter(User.phone_number == message.friend_phone_number).first()
        if user is None or friend is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User or friend not found')
        new_message = Message(
            sender=user.id,
            receiver=friend.id,
            message=message.message,
        )
        db.add(new_message)
        print(f"User: {user.id}, Friend: {friend.id}")
        user_last_message = db.query(Friends).filter(
            ((Friends.friend1 == user.id) & (Friends.friend2 == friend.id)) |
            ((Friends.friend1 == friend.id) & (Friends.friend2 == user.id))
        ).first()
        print(f"Fetched User Last Message: {user_last_message}")
        if user_last_message:
            user_last_message.last_message = message.message
            user_last_message.last_message_type = 'text'
        else:
            user_last_message = Friends(
                friend1=user.id,
                friend2=friend.id,
                last_message=message.message,
                last_message_type='text'  
            )
            db.add(user_last_message)
        db.commit()
        token = db.query(NotificationToken).filter(NotificationToken.user_id == friend.id).first()
        if token:
            print(f"Notification Token: {token.token}")
            send_message_notificaiton(token.token, user.name, message.message, user.profile_picture)
        else:
            print("No notification token found for the friend.")
    except HTTPException as http_exc:
        db.rollback()
        print(f"HTTPException: {str(http_exc)}")
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected Error: {str(e)}")

    return {"message": "Message updated and new entry added successfully"}



class UserStatusResponse(BaseModel):
    status: bool

@router.post('/status', status_code=status.HTTP_200_OK, response_model=UserStatusResponse)
async def change_status(db: db_dependency, phone_number: str):
    user = db.query(User).filter(phone_number == User.phone_number).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Status not updated')
    try:
        user.status = True if user.status else False
        db.commit()        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected Error: {str(e)}")
    
    return UserStatusResponse(
        status=user.status
    )

