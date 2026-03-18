from cachetools import TTLCache

# Shared response cache: 256 entries, 10-minute TTL
response_cache = TTLCache(maxsize=256, ttl=600)
