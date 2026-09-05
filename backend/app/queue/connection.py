from redis import Redis
from rq import Queue, Retry

from app.config import REDIS_URL


redis_conn = Redis.from_url(
    REDIS_URL,
    decode_responses=False,
)

ai_queue = Queue(
    "ai",
    connection=redis_conn,
)

# Retry transient provider/network failures twice without creating a retry storm.
AI_JOB_RETRY = Retry(
    max=2,
    interval=[10, 30],
)
