"""
YouTube Metadata and PO Token Caching Service

Implements Redis-based caching to:
1. Reduce YouTube API requests from 5-15 to 1 per video
2. Cache PO tokens to bypass bot detection
3. Improve download stability across workers
"""
import json
import redis
from typing import Optional, Dict
from app.config.settings import settings
from app.utils.logger import logger


class YouTubeCacheService:
    """Manages Redis caching for YouTube metadata and PO tokens"""
    
    def __init__(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            logger.info("YouTube cache service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube cache service: {e}")
            self.redis_client = None
    
    # ===================================================================
    # METADATA CACHING
    # ===================================================================
    
    def get_cached_metadata(self, video_id: str) -> Optional[Dict]:
        """
        Retrieve cached video metadata from Redis
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Cached metadata dict or None if not found
        """
        if not self.redis_client:
            return None
            
        try:
            key = f"yt:info:{video_id}"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                logger.info(f"✅ Using cached metadata for {video_id}")
                return json.loads(cached_data)
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached metadata for {video_id}: {e}")
            return None
    
    def cache_metadata(self, video_id: str, metadata: Dict, ttl: int = 3600):
        """
        Store video metadata in Redis
        
        Args:
            video_id: YouTube video ID
            metadata: Video metadata dictionary
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        if not self.redis_client:
            return
            
        try:
            key = f"yt:info:{video_id}"
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(metadata)
            )
            logger.info(f"📦 Cached metadata for {video_id} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Error caching metadata for {video_id}: {e}")
    
    # ===================================================================
    # PO TOKEN CACHING
    # ===================================================================
    
    def get_cached_po_token(self, video_id: str) -> Optional[str]:
        """
        Retrieve cached PO (Playback Optimization) token from Redis
        
        PO tokens allow workers to reuse validated playback sessions,
        significantly reducing bot detection and challenge failures.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Cached PO token string or None if not found
        """
        if not self.redis_client:
            return None
            
        try:
            key = f"yt:po_token:{video_id}"
            token = self.redis_client.get(key)
            
            if token:
                logger.info(f"🎫 Using cached PO token for {video_id}")
                return token
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached PO token for {video_id}: {e}")
            return None
    
    def cache_po_token(self, video_id: str, token: str, ttl: int = 3600):
        """
        Store PO token in Redis
        
        Args:
            video_id: YouTube video ID
            token: PO token string
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        if not self.redis_client:
            return
            
        try:
            key = f"yt:po_token:{video_id}"
            self.redis_client.setex(key, ttl, token)
            logger.info(f"🎫 Cached PO token for {video_id} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Error caching PO token for {video_id}: {e}")
    
    # ===================================================================
    # CACHE INVALIDATION
    # ===================================================================
    
    def invalidate_video_cache(self, video_id: str):
        """
        Remove cached data for a specific video
        
        Args:
            video_id: YouTube video ID
        """
        if not self.redis_client:
            return
            
        try:
            keys_to_delete = [
                f"yt:info:{video_id}",
                f"yt:po_token:{video_id}"
            ]
            
            deleted = self.redis_client.delete(*keys_to_delete)
            logger.info(f"🗑️ Invalidated cache for {video_id} ({deleted} keys deleted)")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {video_id}: {e}")


# Global singleton instance
youtube_cache_service = YouTubeCacheService()
