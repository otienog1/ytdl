import storage, { bucketName } from '../config/storage';
import logger from '../utils/logger';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs';

export class StorageService {
  private bucket = storage.bucket(bucketName);

  async uploadFile(localFilePath: string, destinationFileName?: string): Promise<string> {
    try {
      const fileName = destinationFileName || `${uuidv4()}.mp4`;
      const file = this.bucket.file(fileName);

      await this.bucket.upload(localFilePath, {
        destination: fileName,
        metadata: {
          contentType: 'video/mp4',
        },
      });

      logger.info(`File uploaded to GCS: ${fileName}`);

      // Generate signed URL valid for 24 hours
      const [url] = await file.getSignedUrl({
        action: 'read',
        expires: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
      });

      return url;
    } catch (error) {
      logger.error('Error uploading file to GCS:', error);
      throw error;
    }
  }

  async deleteFile(fileName: string): Promise<void> {
    try {
      await this.bucket.file(fileName).delete();
      logger.info(`File deleted from GCS: ${fileName}`);
    } catch (error) {
      logger.error('Error deleting file from GCS:', error);
      throw error;
    }
  }

  async cleanupOldFiles(hoursOld: number = 24): Promise<void> {
    try {
      const [files] = await this.bucket.getFiles();
      const cutoffDate = new Date(Date.now() - hoursOld * 60 * 60 * 1000);

      for (const file of files) {
        const [metadata] = await file.getMetadata();
        const createdDate = new Date(metadata.timeCreated || 0);

        if (createdDate < cutoffDate) {
          await file.delete();
          logger.info(`Cleaned up old file: ${file.name}`);
        }
      }
    } catch (error) {
      logger.error('Error cleaning up old files:', error);
    }
  }
}

export default new StorageService();
