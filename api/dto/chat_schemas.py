from pydantic import BaseModel
from datetime import datetime

# 메시지 생성 요청 DTO
class MessageCreate(BaseModel):
    content: str

# 메시지 읽기 응답 DTO
class MessageRead(BaseModel):
    id: int
    content: str
    timestamp: datetime
    username: str

    class Config:
        from_attributes = True  # ORM 모드 활성화
