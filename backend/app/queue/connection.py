from redis import Redis
from rq import Queue

from app.config import REDIS_URL


redis_conn = Redis.from_url(
    REDIS_URL,
    decode_responses=False,
)

ai_queue = Queue(
    "ai",
    connection=redis_conn,
)
