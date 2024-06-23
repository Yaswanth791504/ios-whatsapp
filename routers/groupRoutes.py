from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from database import session
from typing import Annotated, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Groups, User, GroupMembers
# from routers.firebase_notifications import send_group_notification


router = APIRouter(
    prefix='/group',
    tags=['group']
)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()
    
db_dependency = Annotated[Session, Depends(get_db)]


class GroupRequest(BaseModel):
    group_name: str
    members: List[str]
    group_description: str
    admin_phone_number: str
    profile_picture: str

class GroupResponse(BaseModel):
    group_id: int

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_group(db: db_dependency, group: GroupRequest):
    admin = db.query(User).filter(User.phone_number == group.admin_phone_number).first()
    if admin is None:
        raise HTTPException(status_code=404, detail='User not found')
    try:
        newGroup = Groups(
            group_name=group.group_name,
            group_description=group.group_description,
            admin=admin.id,
            profile_picture=group.profile_picture
        )
        db.add(newGroup)
        db.commit()
        for member in group.members:
            user = db.query(User).filter(User.phone_number == member).first()
            if user is None:
                raise HTTPException(status_code=404, detail='User not found')
            newMember = GroupMembers(
                group_id=newGroup.id,
                user_id=user.id
            )
            db.add(newMember)
            db.commit()
        return GroupResponse(group_id=newGroup.id)
    except Exception as e:
        raise e
    
@router.put("/", status_code=status.HTTP_202_ACCEPTED)
async def update_group(db: db_dependency, group_id: int, group: GroupRequest): 
    group = db.query(Groups).filter(group_id == Groups.id).first()
    if group is None:
        raise HTTPException(status_code=404, detail='Group not found')
    try:
        group.group_name = group.group_name
        group.group_description = group.group_description
        group.profile_picture = group.profile_picture
        db.commit()
        return {"message": "Group updated"}
    except Exception as e:
        raise e
    