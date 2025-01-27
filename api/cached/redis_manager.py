import redis
from sqlalchemy.orm import Session
from config.models import Member

class RedisManager:

    def __init__(self, host: str = "localhost", port: int = 6379, password: str = None):
        self.client = redis.StrictRedis(
            host=host,
            port=port,
            password=password,
            decode_responses=True
        )

    def cache_message(self, room_id: int, message: str, max_messages: int = 50):
        """
        특정 채팅방의 메시지 캐싱
        """
        key = f"chatroom:{room_id}"
        self.client.lpush(key, message)
        self.client.ltrim(key, 0, max_messages - 1)

    def get_cached_messages(self, room_id: int):
        """
        특정 채팅방의 캐싱된 메시지 조회
        """
        key = f"chatroom:{room_id}"
        return self.client.lrange(key, 0, -1)

    def increment_hate_count(self, user_id: int, max_limit: int = 3) -> bool:
        """
        유저의 혐오 표현 경고 횟수 증가 및 차단 여부 확인
        """
        key = f"user:{user_id}:hate_count"
        count = self.client.incr(key)

        if count == 1:
            self.client.expire(key, 3600)  # 초기 TTL 설정

        return count >= max_limit

    def get_hate_count(self, user_id: int) -> int:
        """
        유저의 혐오 표현 경고 횟수 조회
        """
        key = f"user:{user_id}:hate_count"
        return int(self.client.get(key) or 0)

    def reset_hate_count(self, user_id: int):
        """
        유저의 혐오 표현 경고 횟수 초기화
        """
        key = f"user:{user_id}:hate_count"
        self.client.delete(key)

    def check_ban_status(self, user_id: int) -> bool:
        """
        유저 차단 상태 확인
        """
        key = f"user:{user_id}:is_banned"
        status = self.client.get(key)
        return status == "1"

    def sync_hate_data_to_db(self, user_id: int, db: Session, max_limit: int = 3):
        """
        Redis의 혐오 데이터를 DB와 동기화
        """
        count = self.get_hate_count(user_id)
        user = db.query(Member).filter(Member.id == user_id).first()

        if user:
            user.warnings = count
            if count >= max_limit:
                user.is_blocked = True
            db.commit()
