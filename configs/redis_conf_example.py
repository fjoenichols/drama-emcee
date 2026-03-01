"""
Example Redis connection config.
Copy this file to configs/redis_conf.py and fill in your credentials.
"""

import redis

r = redis.Redis(
    host="[ redis-hostname ]",
    port=6379,
    username="[ redis username ]",
    password="[ redis password ]",
    ssl=True,
    decode_responses=True,
)
