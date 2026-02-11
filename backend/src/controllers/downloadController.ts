import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import Download from '../models/Download';
import downloadQueue from '../queue/downloadQueue';
import { downloadRequestSchema } from '../utils/validators';
import logger from '../utils/logger';
import type { DownloadResponse } from '../types';

export class DownloadController {
  async initiateDownload(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const validatedData = downloadRequestSchema.parse(req.body);
      const { url } = validatedData;

      const jobId = uuidv4();

      // Create download record
      const download = await Download.create({
        url,
        jobId,
        status: 'queued',
        progress: 0,
      });

      // Add to queue
      await downloadQueue.add({
        url,
        jobId,
      });

      logger.info(`Download initiated: ${jobId} for URL: ${url}`);

      const response: DownloadResponse = {
        jobId,
        status: 'queued',
      };

      res.status(202).json(response);
    } catch (error: any) {
      if (error.name === 'ZodError') {
        res.status(400).json({
          error: 'Validation error',
          details: error.errors,
        });
      } else {
        next(error);
      }
    }
  }

  async getDownloadStatus(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { jobId } = req.params;

      const download = await Download.findOne({ jobId });

      if (!download) {
        res.status(404).json({
          error: 'Download not found',
          message: 'The requested download job does not exist',
        });
        return;
      }

      const response: DownloadResponse = {
        jobId: download.jobId,
        status: download.status,
        videoInfo: download.videoInfo,
        downloadUrl: download.downloadUrl,
        error: download.error,
      };

      res.json(response);
    } catch (error) {
      next(error);
    }
  }

  async getDownloadHistory(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || 10;
      const downloads = await Download.find()
        .sort({ createdAt: -1 })
        .limit(limit);

      res.json(downloads);
    } catch (error) {
      next(error);
    }
  }
}

export default new DownloadController();
