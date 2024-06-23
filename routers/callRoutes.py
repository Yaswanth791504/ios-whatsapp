from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette import status
from database import session
from typing import Annotated, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, Calls, NotificationToken
from datetime import datetime
from routers.firebase_notifications import send_call_ring

router = APIRouter(
    prefix="/calls",
    tags=["calls"]
)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()
    
db_dependency = Annotated[Session, Depends(get_db)]

class UserCall(BaseModel):
    friend_phone_number: str
    call_type: str
    call_id: str

class UserResponseCall(BaseModel):
    caller_id: int
        
@router.post("/", status_code=status.HTTP_201_CREATED)
async def phone_call(db: db_dependency, phone_number: str, call: UserCall):
    user = db.query(User).filter(phone_number == User.phone_number).first()
    friend = db.query(User).filter(call.friend_phone_number == User.phone_number).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user is not found')
    try:
        newCall = Calls(
            caller=user.id,
            receiver=friend.id,
            call_type=call.call_type,
            callid=call.call_id
        )
        db.add(newCall)
        db.commit()
        token = db.query(NotificationToken).filter(friend.id == NotificationToken.user_id).first()
        send_call_ring(token.token, f"Incoming {'audio' if call.call_type == 'phonecall' else 'video'} call", user.name, user.profile_picture, call_id=call.call_id, type=call.call_type)
        return UserResponseCall(caller_id=newCall.id)
    except Exception as e:
        raise e

@router.put("/", status_code=status.HTTP_202_ACCEPTED)
async def update_phonecall_duration(db: db_dependency, caller_id: int, duration: int):
    call = db.query(Calls).filter(caller_id == Calls.id).first()
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='call is not found')
    try:
        call.duration = duration
        db.commit()
        return {"message": "call duration updated"}
    except Exception as e:
        raise e

class CallResponse(BaseModel):
    profile_picture: str
    name: str
    phone_number: str
    call_type: str
    started_at: datetime
    sent: bool
    caller_id: int


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[CallResponse])
async def get_calls(db: db_dependency, phone_number: str):
    user = db.query(User).filter(phone_number == User.phone_number).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user is not found')
    try:
        caller_calls = db.query(Calls).filter(user.id == Calls.caller).all()
        receiver_calls = db.query(Calls).filter(user.id == Calls.receiver).all()
        call_list = []
        for call in caller_calls:
            friend = db.query(User).filter(call.receiver == User.id).first()
            call_list.append(CallResponse(
                profile_picture=friend.profile_picture,
                name=friend.name,
                phone_number=friend.phone_number,
                call_type=call.call_type,
                started_at=call.started_at,
                
                sent=True,
                caller_id=call.id
            ))
        for call in receiver_calls:
            friend = db.query(User).filter(call.caller == User.id).first()
            call_list.append(CallResponse(
                profile_picture=friend.profile_picture,
                name=friend.name,
                phone_number=friend.phone_number,
                call_type=call.call_type,
                started_at=call.started_at,
                duration=call.duration,
                sent=False,
                caller_id=call.id
            ))
        call_list.sort(key=lambda x: x.started_at, reverse=True)
        return call_list
    except Exception as e:
        raise e


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(db: db_dependency, caller_id: str):
    call = db.query(Calls).filter(int(caller_id) == Calls.id).first()
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='call is not found')
    try:
        db.delete(call)
        db.commit()
        
        return
    except Exception as e:
        raise e
