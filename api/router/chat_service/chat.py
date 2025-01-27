from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dto.chat_schemas import MessageCreate, MessageRead, ChatRoomRead

from utils.connection_manager import ConnectManager
from cached.redis_manager import RedisManager

from datetime import datetime

from config.database import get_db
from config.models import Message, Member

from security.jwt import decode_access_token

from .classify_text import classify_text

chat_router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

manager = ConnectManager()
redis = RedisManager()

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
            .filter(Message.chat_room_id == room.id)
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

        # 사용자 차단 상태 확인
        if redis.check_ban_status(user.id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=403, detail="User is banned")

        # 채팅방 존재 여부 확인
        chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not chat_room:
            raise HTTPException(status_code=404, detail="Chat room not found")

        await manager.connect(websocket)
        print(f"User {username} connected to room {room_id}")

        while True:
            data = await websocket.receive_json()
            content = data.get("message")

            if not content:
                await websocket.send_json({"error": "Empty message"})
                continue

            # 혐오 표현 감지
            classify_result = await classify_text([content])
            label = classify_result[0]["label"]

            if label == "혐오":
                # Redis에서 경고 횟수 증가 및 차단 여부 확인
                is_banned = redis.hate_count(user.id)

                if is_banned:
                    await manager.broadcast({
                        "username": username,
                        "content": "사용자가 차단되었습니다.",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                    })
                    redis.sync_hate_data_to_db(user.id, db)  # DB 동기화
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    continue

                warning_count = redis.get_current_hate_count(user.id)
                await manager.broadcast({
                    "username": username,
                    "content": f"경고 {warning_count}/3: 혐오 표현이 감지되었습니다.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "room_id": room_id,
                })
                continue

            # 메시지 저장
            message = Message(content=content, user_id=user.id, chat_room_id=room_id)
            db.add(message)
            db.commit()

            # 메시지 캐싱
            redis.cache_message(room_id, content)

            await manager.broadcast({
                "username": username,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id,
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"User {username} disconnected from room {room_id}")

    except Exception as e:
        print(f"Error: {e}")
        await websocket.close(code=1008)
