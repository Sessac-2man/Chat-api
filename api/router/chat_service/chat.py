from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from dto.chat_schemas import MessageCreate, MessageRead, ChatRoomRead, CreateChatRoomPayload


from utils.connection_manager import ConnectManager
from cached.redis_manager import RedisManager

from datetime import datetime

from config.database import get_db
from config.models import Message, Member, ChatRoom

from security.auth import *

from security.jwt import decode_access_token

from .classify_text import classify_text

chat_router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

manager = ConnectManager()
redis = RedisManager()


# 채팅방 생성


@chat_router.post("/rooms")
def create_chat_room(
    payload: CreateChatRoomPayload,
    db: Session = Depends(get_db),
    current_user: Member = Depends(get_current_user)
):
    # 중복 이름 확인
    existing_room = db.query(ChatRoom).filter(ChatRoom.name == payload.room_name).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Chat room name already exists")

    # 채팅방 생성
    chat_room = ChatRoom(
        name=payload.room_name,
        created_by=current_user.id
    )
    db.add(chat_room)
    db.commit()
    db.refresh(chat_room)

    # 현재 사용자를 채팅방 멤버로 추가
    chat_room.members.append(current_user)
    db.commit()

    return {
        "id": chat_room.id,
        "name": chat_room.name,
        "created_at": chat_room.created_at,
    }



# 채팅방 멤버 초대
@chat_router.post("/rooms/{room_id}/invite")
def invite_member_to_chat_room(room_id: int, member_id: int, db: Session = Depends(get_db)):
    """
    채팅방에 멤버 초대
    """
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member in chat_room.members:
        raise HTTPException(status_code=400, detail="Member is already in the chat room")

    chat_room.members.append(member)
    db.commit()
    return {"message": f"Member {member.username} added to chat room {chat_room.name}"}

# 채팅방 나가기
@chat_router.post("/rooms/{room_id}/leave")
def leave_chat_room(room_id: int, member_id: int, db: Session = Depends(get_db)):
    """
    채팅방 나가기
    """
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member not in chat_room.members:
        raise HTTPException(status_code=400, detail="Member is not part of the chat room")

    chat_room.members.remove(member)
    db.commit()
    return {"message": f"Member {member.username} has left the chat room {chat_room.name}"}


# 채팅방 조회
@chat_router.get("/rooms", response_model=list[ChatRoomRead])
def get_chat_rooms(current_user: Member = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    현재 로그인한 사용자의 채팅방 목록 반환
    """
    chat_rooms = (
        db.query(ChatRoom)
        .filter(ChatRoom.members.any(id=current_user.id))
        .all()
    )

    response = []
    for room in chat_rooms:
        last_message = (
            db.query(Message.content)
            .filter(Message.chat_room_id == room.id)
            .order_by(Message.timestamp.desc())
            .first()
        )

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
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str, db: Session = Depends(get_db)):
    await websocket.accept()

    try:
        # JWT 토큰 검증
        payload = decode_access_token(token)
        if not payload:
            await websocket.send_json({"error": "Invalid token"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        username = payload.get("sub")
        user = db.query(Member).filter(Member.username == username).first()
        if not user:
            await websocket.send_json({"error": "User not found"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 🚨 Redis에서 사용자의 차단 상태 확인
        is_banned = redis.check_ban_status(user.id)
        if is_banned is None:
            # Redis에 데이터가 없으면 DB에서 가져와 Redis에 동기화
            is_banned = user.is_blocked or False
            redis.client.set(f"user:{user.id}:is_banned", "1" if is_banned else "0")

        # 차단된 경우 연결을 종료하고 에러 메시지를 보냄
        if is_banned:
            await websocket.send_json({"error": "User is banned"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 채팅방 존재 여부 확인
        chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not chat_room:
            await websocket.send_json({"error": "Chat room not found"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 사용자 WebSocket 연결
        await manager.connect(websocket, room_id)
        print(f"User {username} connected to room {room_id}")

        while True:
            data = await websocket.receive_json()
            content = data.get("message")
            msg_type = data.get("type", "message")

            if msg_type == "pong":
                continue

            if not content:
                await websocket.send_json({"error": "Empty message"})
                continue

            # 혐오 표현 필터링
            classify_result = await classify_text([content])
            label = classify_result[0]["label"]

            if label == "혐오":
                is_banned = redis.increment_hate_count(user.id)
                if is_banned:
                    await manager.broadcast({
                        "username": "System",
                        "content": f"{username}님이 차단되었습니다.",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                    }, room_id)
                    redis.sync_hate_data_to_db(user.id, db)
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return

                warning_count = redis.get_hate_count(user.id)
                await manager.broadcast({
                    "username": "System",
                    "content": f"경고 {warning_count}/3: 혐오 표현이 감지되었습니다.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "room_id": room_id,
                }, room_id)
                continue

            # 메시지 저장 및 브로드캐스트
            message = Message(content=content, user_id=user.id, chat_room_id=room_id)
            db.add(message)
            db.commit()

            await manager.broadcast({
                "username": username,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id,
            }, room_id)

    except WebSocketDisconnect:
        print(f"User {username} disconnected from room {room_id}")
        manager.disconnect(websocket, room_id)

    except Exception as e:
        print(f"Unexpected error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

    finally:
        print(f"WebSocket connection with {username} closed.")



@chat_router.get("/rooms/{room_id}/messages")
def get_messages(room_id: int, db: Session = Depends(get_db), current_user: Member = Depends(get_current_user)):
    """
    채팅방 메시지 조회
    """
    # 채팅방 존재 여부 확인
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # 사용자가 해당 채팅방의 멤버인지 확인
    if current_user not in chat_room.members:
        raise HTTPException(status_code=403, detail="User is not a member of this chat room")

    # 채팅방 메시지 조회
    messages = (
        db.query(Message)
        .filter(Message.chat_room_id == room_id)
        .order_by(Message.timestamp.asc())  # 시간순 정렬
        .all()
    )

    # 메시지 목록 반환
    return [
        {
            "id": message.id,
            "username": db.query(Member.username).filter(Member.id == message.user_id).scalar(),
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
        }
        for message in messages
    ]
