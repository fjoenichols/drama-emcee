# This is an example of what your configs/redis_conf.py should look like
import redis

r = redis.Redis(
        host="[ redis-hostname ]", port=[ redis port ],
        username="[ redis username ]",
        password="[ redis password ]",
        ssl=True,
        decode_responses=True
)
