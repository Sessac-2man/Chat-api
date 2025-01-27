import redis
from sqlalchemy.orm import Session
from config.models import Member

class RedisManager:

    def __init__(self, host: str = "localhost", port: int = 6379, password: str = None):
        self.client = redis.StrictRedis(
            host=host,
            port=port,
            password="redis1234",
            decode_responses=True  # 문자열 디코딩
        )

    def cache_message(self, room_id: int, message: str, max_massages: int = 50):
        """
        특정 채팅방의 메시지 캐싱
        """
        key = f"chatroom:{room_id}"
        self.client.lpush(key, message)
        self.client.ltrim(key, 0, max_massages - 1)  # 최신 메시지 개수 유지

    def get_cached_messages(self, room_id: int):
        """
        특정 채팅방 내 캐싱된 메시지 조회
        """
        key = f"chatroom:{room_id}"
        return self.client.lrange(key, 0, -1)

    def hate_count(self, user_id: int, max_limit: int = 3):
        """
        경고 횟수 증가 및 차단 여부 확인
        """
        key = f"user:{user_id}:hate_count"
        count = self.client.incr(key)  # 카운트 증가

        if count == 1:
            self.client.expire(key, 3600)  # 초기 생성 시 1시간 TTL 설정
        return count >= max_limit

    def reset_hate_count(self, user_id: int):
        """
        경고 횟수 초기화
        """
        key = f"user:{user_id}:hate_count"
        self.client.delete(key)

    def sync_hate_data_to_db(self, user_id: int, db: Session, max_limit: int = 3):
        """
        Redis의 경고 데이터를 DB와 동기화
        """
        count = int(self.client.get(f"user:{user_id}:hate_count") or 0)

        user = db.query(Member).filter(Member.id == user_id).first()

        if user:
            user.warning_count = count
            if count >= max_limit:
                user.is_banned = True
            db.commit()

    def set_ban_status(self, user_id: int, is_banned: bool):
        """
        사용자의 차단 상태 설정
        """
        key = f"user:{user_id}:is_banned"
        self.client.set(key, "1" if is_banned else "0")

    def check_ban_status(self, user_id: int) -> bool:
        """
        차단 상태 확인
        """
        key = f"user:{user_id}:is_banned"
        status = self.client.get(key)
        return status == "1"  # Redis에 저장된 값이 "1"이면 차단 상태

    def unban_user(self, user_id: int):
        """
        사용자의 차단 해제
        """
        key = f"user:{user_id}:is_banned"
        self.client.set(key, "0")  # 차단 해제
