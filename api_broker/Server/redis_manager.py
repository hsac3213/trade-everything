import redis

REDIS_HOST = "localhost"
REDIS_PORT = 6379

class RedisManager:
    def __init__(self):
        # 일반 데이터(json) 저장용 클라이언트
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True
        )
        # Challenge(binary 형태) 저장용 클라이언트
        self.redis_client_binary = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            # Bytes 디코딩 비활성화 필요
            decode_responses=False
        )
        try:
            self.redis_client.ping()
            self.redis_client_binary.ping()
            print("Redis connected.")
        except redis.ConnectionError:
            print("Redis connection error.")
            raise