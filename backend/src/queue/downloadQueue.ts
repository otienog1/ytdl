import Bull, { Job, Queue } from 'bull';
import redis from '../config/redis';
import logger from '../utils/logger';
import Download from '../models/Download';
import youtubeService from '../services/youtubeService';
import storageService from '../services/storageService';
import { extractVideoId } from '../utils/validators';

interface DownloadJobData {
  url: string;
  jobId: string;
}

// Parse Redis URL properly for Bull
const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
const redisUrlObj = new URL(redisUrl);

const redisOptions: any = {
  host: redisUrlObj.hostname,
  port: parseInt(redisUrlObj.port) || 6379,
};

// Add password if present
if (redisUrlObj.password) {
  redisOptions.password = redisUrlObj.password;
}

// Only enable TLS if explicitly using rediss://
// Note: Redis Cloud works with redis:// (non-TLS) for some configurations
if (redisUrl.startsWith('rediss://')) {
  redisOptions.tls = {
    rejectUnauthorized: false,
  };
}

// Debug: log what we're connecting with (remove password for security)
logger.info('Bull Queue Redis Config:', {
  host: redisOptions.host,
  port: redisOptions.port,
  hasTLS: !!redisOptions.tls,
  hasPassword: !!redisOptions.password,
});

const downloadQueue: Queue<DownloadJobData> = new Bull('video-download', {
  redis: redisOptions,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 5000,
    },
    removeOnComplete: 100,
    removeOnFail: 100,
  },
});

downloadQueue.process(async (job: Job<DownloadJobData>) => {
  const { url, jobId } = job.data;

  try {
    logger.info(`Processing download job: ${jobId}`);

    // Update status to processing
    await Download.findOneAndUpdate(
      { jobId },
      { status: 'processing', progress: 10 }
    );

    job.progress(10);

    // Get video info
    const videoId = extractVideoId(url);
    if (!videoId) {
      throw new Error('Invalid video URL');
    }

    logger.info(`Fetching video info for: ${videoId}`);
    const videoInfo = await youtubeService.getVideoInfo(url);

    await Download.findOneAndUpdate(
      { jobId },
      { videoInfo, progress: 30 }
    );

    job.progress(30);

    // Download video
    logger.info(`Downloading video: ${videoId}`);
    const localFilePath = await youtubeService.downloadVideo(url, videoId);

    await Download.findOneAndUpdate(
      { jobId },
      { progress: 70 }
    );

    job.progress(70);

    // Upload to cloud storage
    logger.info(`Uploading video to cloud storage: ${videoId}`);
    const downloadUrl = await storageService.uploadFile(localFilePath);

    await Download.findOneAndUpdate(
      { jobId },
      { progress: 90 }
    );

    job.progress(90);

    // Clean up local file
    await youtubeService.deleteLocalFile(localFilePath);

    // Update status to completed
    await Download.findOneAndUpdate(
      { jobId },
      {
        status: 'completed',
        progress: 100,
        downloadUrl,
      }
    );

    logger.info(`Download job completed: ${jobId}`);

    return { jobId, status: 'completed', downloadUrl, videoInfo };
  } catch (error: any) {
    logger.error(`Download job failed: ${jobId}`, error);

    await Download.findOneAndUpdate(
      { jobId },
      {
        status: 'failed',
        error: error.message || 'Unknown error occurred',
      }
    );

    throw error;
  }
});

downloadQueue.on('completed', (job, result) => {
  logger.info(`Job ${job.id} completed with result:`, result);
});

downloadQueue.on('failed', (job, error) => {
  logger.error(`Job ${job?.id} failed with error:`, error);
});

downloadQueue.on('error', (error) => {
  logger.error('Queue error:', error);
});

export default downloadQueue;
