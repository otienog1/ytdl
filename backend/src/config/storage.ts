import { Storage } from '@google-cloud/storage';
import logger from '../utils/logger';

let storage: Storage;

try {
  const projectId = process.env.GCP_PROJECT_ID;
  const keyFilename = process.env.GOOGLE_APPLICATION_CREDENTIALS;

  if (!projectId) {
    logger.warn('GCP_PROJECT_ID not set. Google Cloud Storage features will be limited.');
  }

  storage = new Storage({
    projectId,
    keyFilename,
  });

  logger.info('Google Cloud Storage initialized');
} catch (error) {
  logger.error('Failed to initialize Google Cloud Storage:', error);
  throw error;
}

export const bucketName = process.env.GCP_BUCKET_NAME || 'shorts-downloader-temp';

export default storage;
