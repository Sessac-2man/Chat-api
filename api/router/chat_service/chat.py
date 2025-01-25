from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dto.chat_schemas import MessageCreate, MessageRead

from utils.connection_manager import ConnectManager

from config.database import get_db
from config.models import Message, Member
from security.jwt import decode_access_token


chat_router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

manager = ConnectManager()

@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket 연결 엔드포인트 (JWT 검증 포함)
    """
    try:
        # JWT 검증
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        username = payload.get("sub")
        db: Session = next(get_db())
        user = db.query(Member).filter(Member.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        # WebSocket 연결 관리
        await manager.connect(websocket)
        print(f"User {username} connected")

        # 메시지 송수신
        while True:
            data = await websocket.receive_json()
            message_data = MessageCreate(**data)  # DTO로 데이터 검증

            # 메시지 저장
            message = Message(content=message_data.content, user_id=user.id)
            db.add(message)
            db.commit()

            # 브로드캐스트 메시지
            broadcast_message = MessageRead(
                id=message.id,
                content=message.content,
                timestamp=message.timestamp,
                username=user.username,
            )
            await manager.broadcast(broadcast_message.dict())

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"User {username} disconnected")

    except Exception as e:
        print(f"Error: {e}")
        manager.disconnect(websocket)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
