from database import Base
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Interval, Boolean, CheckConstraint
from sqlalchemy.sql import func

# user model
class User(Base):
    __tablename__='users'

    id=Column(Integer, unique=True, primary_key=True)
    name=Column(String(50))
    email=Column(String)
    profile_picture=Column(String)
    phone_number=Column(String(20), unique=True)
    about=Column(String(100))
    created_at=Column(DateTime(timezone=False), default=func.now())
    update_at=Column(DateTime(timezone=False), default=func.now(), onupdate=func.now())
    status=Column(Boolean, default=False)
    
 #  messages model
class Message(Base):
    __tablename__="messages"
    
    id=Column(Integer, unique=True, primary_key=True)
    receiver=Column(Integer, ForeignKey("users.id"))
    sender=Column(Integer, ForeignKey("users.id"))
    message=Column(String)
    sent_at=Column(DateTime(timezone=False), default=func.now())

#  friends model
class Friends(Base):
    __tablename__="friends"

    id=Column(Integer, unique=True, primary_key=True)
    friend1=Column(Integer, ForeignKey("users.id"), unique=True)
    friend2=Column(Integer, ForeignKey("users.id"), unique=True)
    friends_since=Column(DateTime(timezone=False), default=func.now())
    last_message=Column(String)
    last_message_time=Column(DateTime(timezone=False), default=func.now())
    last_message_type=Column(String, default="text")

# phone call model
class Calls(Base):
    __tablename__="calls"

    id=Column(Integer, unique=True, primary_key=True)
    caller=Column(Integer, ForeignKey("users.id"))
    receiver=Column(Integer, ForeignKey("users.id"))
    started_at=Column(DateTime(timezone=False), default=func.now())
    duration=Column(Interval, default=None)
    call_type=Column(String, nullable=False, default='phonecall')
    callid=Column(String, nullable=False)
    
# groups model
class Groups(Base):
    __tablename__="groups"

    id=Column(Integer, unique=True, primary_key=True)
    admin_id=Column(Integer, ForeignKey("users.id"))
    created_at=Column(DateTime(timezone=False), default=func.now())

#  Group member model
class GroupMembers(Base):
    __tablename__="groupmembers"

    id=Column(Integer, unique=True, primary_key=True)
    group_id=Column(Integer, ForeignKey("groups.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    
# class Notification token
class NotificationToken(Base):
    __tablename__ = "notificationtoken"

    id=Column(Integer, unique=True, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id", ondelete="cascade"), unique=True, nullable=False)
    token=Column(String, nullable=False)
    
#  Media class 
class Media(Base):
    __tablename__="media"

    id=Column(Integer, unique=True, primary_key=True)
    sender=Column(Integer, ForeignKey("users.id"))
    receiver=Column(Integer, ForeignKey("users.id"))
    media_link=Column(String, nullable=False)
    media_type=Column(String, nullable=False)
    sent_at=Column(DateTime(timezone=False), default=func.now())

class Status(Base):
    __tablename__ = 'status'

    id=Column(Integer, unique=True, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id", ondelete='Cascade'), nullable=False)
    status_link=Column(String, nullable=True)
    status_text=Column(String, nullable=True)
    uploaded_at=Column(DateTime(timezone=False), default=func.now())
    status_type=Column(String, nullable=False, default='text')
    status_text_color=Column(String, nullable=True)

    __tableargs__ = (
        CheckConstraint(
            'status_text IS NOT NULL OR status_link IS NOT NULL',
            name='status_not_null'
        )
    )


