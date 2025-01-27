from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# 다 대 다 관계 매핑
chat_room_members = Table(
    'chat_room_members',
    Base.metadata,
    Column('chat_room_id', ForeignKey('chat_rooms.id'), primary_key=True),
    Column('member_id', ForeignKey('members.id'), primary_key=True)
)

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    warnings = Column(Integer, default=0)  # 경고 횟수
    is_blocked = Column(Boolean, default=False)  # 차단 여부

    # Relationships
    messages = relationship("Message", back_populates="owner")
    chat_rooms = relationship("ChatRoom", secondary=chat_room_members, back_populates="members")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)

    # Relationships
    owner = relationship("Member", back_populates="messages")
    chat_room = relationship("ChatRoom", back_populates="messages")

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    messages = relationship("Message", back_populates="chat_room")
    members = relationship("Member", secondary=chat_room_members, back_populates="chat_rooms")
