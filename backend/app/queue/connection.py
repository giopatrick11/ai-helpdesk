from redis import Redis
from rq import Queue


redis_conn = Redis(
    host="localhost",
    port=6379,
    decode_responses=False,
)

ai_queue = Queue(
    "ai",
    connection=redis_conn,
)