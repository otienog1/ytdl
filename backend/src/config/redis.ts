import Redis from "ioredis";
import logger from "../utils/logger";

const redisUrl = process.env.REDIS_URL || "redis://localhost:6379";

// Configure Redis connection for ioredis
// For Redis Cloud, use rediss:// URL or the connection will use TLS automatically
const redis = new Redis(redisUrl, {
  maxRetriesPerRequest: 3,
  enableReadyCheck: true,
  retryStrategy(times: number) {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  // ioredis automatically handles TLS when URL starts with rediss://
  // No need for explicit tls configuration
});

redis.on("connect", () => {
  logger.info("Redis connected successfully");
});

redis.on("error", (error) => {
  logger.error("Redis connection error:", error);
});

redis.on("close", () => {
  logger.warn("Redis connection closed");
});

export default redis;
