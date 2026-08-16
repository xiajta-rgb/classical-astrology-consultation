import os
import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

DEFAULT_TTL = 3600
SHORT_TTL = 300
LONG_TTL = 86400

_redis_client = None

def get_redis_client():
    global _redis_client
    
    if not REDIS_ENABLED:
        return None
    
    if not REDIS_AVAILABLE:
        logger.warning("Redis library not available. Install with: pip install redis")
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            _redis_client.ping()
            logger.info(f"Redis连接成功: {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis连接失败: {e}，缓存功能将不可用")
            _redis_client = None
        except Exception as e:
            logger.warning(f"Redis初始化异常: {e}，缓存功能将不可用")
            _redis_client = None
    
    return _redis_client

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    key_parts = [prefix]
    
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}={v}")
    
    key_str = ":".join(key_parts)
    
    if len(key_str) > 200:
        hash_suffix = hashlib.md5(key_str.encode()).hexdigest()[:16]
        key_str = f"{prefix}:{hash_suffix}"
    
    return key_str

def cache_key(prefix: str, *key_fields):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_values = []
            for i, field in enumerate(key_fields):
                if isinstance(field, int):
                    if i < len(args):
                        key_values.append(str(args[i]))
                    else:
                        key_values.append(str(kwargs.get(field, "")))
                else:
                    key_values.append(str(kwargs.get(field, "")))
            
            cache_key = generate_cache_key(prefix, *key_values)
            
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_value = redis_client.get(cache_key)
                    if cached_value:
                        logger.debug(f"缓存命中: {cache_key}")
                        return json.loads(cached_value)
                except Exception as e:
                    logger.warning(f"缓存读取失败: {e}")
            
            result = func(*args, **kwargs)
            
            if redis_client and result is not None:
                try:
                    redis_client.setex(
                        cache_key,
                        DEFAULT_TTL,
                        json.dumps(result, ensure_ascii=False, default=str)
                    )
                    logger.debug(f"缓存写入: {cache_key} (TTL: {DEFAULT_TTL}s)")
                except Exception as e:
                    logger.warning(f"缓存写入失败: {e}")
            
            return result
        return wrapper
    return decorator

def cached(prefix: str, ttl: int = DEFAULT_TTL):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_value = redis_client.get(cache_key)
                    if cached_value:
                        logger.debug(f"缓存命中: {cache_key}")
                        return json.loads(cached_value)
                except Exception as e:
                    logger.warning(f"缓存读取失败: {e}")
            
            result = func(*args, **kwargs)
            
            if redis_client and result is not None:
                try:
                    redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, ensure_ascii=False, default=str)
                    )
                    logger.debug(f"缓存写入: {cache_key} (TTL: {ttl}s)")
                except Exception as e:
                    logger.warning(f"缓存写入失败: {e}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str) -> int:
    redis_client = get_redis_client()
    if not redis_client:
        return 0
    
    try:
        keys = list(redis_client.scan_iter(match=pattern))
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"缓存失效: {pattern}, 删除 {deleted} 个键")
            return deleted
        return 0
    except Exception as e:
        logger.warning(f"缓存失效失败: {e}")
        return 0

def get_cache_stats() -> dict:
    redis_client = get_redis_client()
    if not redis_client:
        return {"enabled": False, "available": False}
    
    try:
        info = redis_client.info("stats")
        return {
            "enabled": True,
            "available": True,
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "N/A"),
        }
    except Exception as e:
        return {"enabled": True, "available": False, "error": str(e)}
