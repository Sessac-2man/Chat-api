from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dto.chat_schemas import MessageCreate, MessageRead, ChatRoomRead

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

# 채팅방 조회
@chat_router.get("/rooms", response_model=list[ChatRoomRead])
def get_chat_rooms(user_id: int, db: Session = Depends(get_db)):
    """
    사용자와 연결된 채팅방 목록 반환
    """
    # 사용자와 연결된 채팅방 조회
    chat_rooms = (
        db.query(ChatRoom)
        .filter(ChatRoom.members.any(id=user_id))
        .all()
    )

    # 채팅방 데이터를 DTO로 변환
    response = []
    for room in chat_rooms:
        # 채팅방의 마지막 메시지 가져오기
        last_message = (
            db.query(Message.content)
            .filter(Message.room_id == room.id)
            .order_by(Message.timestamp.desc())
            .first()
        )

        # ChatRoomRead DTO로 변환
        response.append(
            ChatRoomRead(
                id=room.id,
                name=room.name,
                created_at=room.created_at,
                last_message=last_message[0] if last_message else None
            )
        )

    return response


# 채팅방 접속

@chat_router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str):
    """
    특정 채팅방 WebSocket 연결
    """
    try:
        # JWT 검증
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        username = payload.get("sub")
        db: Session = next(get_db())
        user = db.query(Member).filter(Member.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # 채팅방 존재 여부 확인
        chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not chat_room:
            raise HTTPException(status_code=404, detail="Chat room not found")

        # WebSocket 연결 관리
        await manager.connect(websocket)
        print(f"User {username} connected to room {room_id}")

        # 메시지 송수신
        while True:
            data = await websocket.receive_json()
            content = data.get("message")

            # 메시지 저장
            message = Message(content=content, user_id=user.id, room_id=room_id)
            db.add(message)
            db.commit()

            # 브로드캐스트 메시지
            broadcast_message = {
                "username": username,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id,
            }
            await manager.broadcast(broadcast_message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"User {username} disconnected from room {room_id}")

    except Exception as e:
        print(f"Error: {e}")
        await websocket.close(code=1008)



