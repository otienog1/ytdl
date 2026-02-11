import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';
import logger from '../utils/logger';
import type { VideoInfo } from '../types';

const execAsync = promisify(exec);

export class YouTubeService {
  private downloadDir = path.join(process.cwd(), 'downloads');

  constructor() {
    this.ensureDownloadDir();
  }

  private async ensureDownloadDir(): Promise<void> {
    try {
      await fs.mkdir(this.downloadDir, { recursive: true });
    } catch (error) {
      logger.error('Error creating download directory:', error);
    }
  }

  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      const { stdout } = await execAsync(
        `yt-dlp --dump-json --no-playlist "${url}"`
      );

      const info = JSON.parse(stdout);

      return {
        id: info.id,
        title: info.title,
        thumbnail: info.thumbnail,
        duration: info.duration,
        quality: info.height ? `${info.height}p` : undefined,
        fileSize: info.filesize ? this.formatFileSize(info.filesize) : undefined,
      };
    } catch (error) {
      logger.error('Error fetching video info:', error);
      throw new Error('Failed to fetch video information');
    }
  }

  async downloadVideo(url: string, videoId: string): Promise<string> {
    try {
      const fileName = `${videoId}_${uuidv4()}.mp4`;
      const outputPath = path.join(this.downloadDir, fileName);

      // Download best quality video+audio merged into mp4
      const command = `yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 -o "${outputPath}" "${url}"`;

      logger.info(`Executing download command for video: ${videoId}`);
      await execAsync(command);

      logger.info(`Video downloaded successfully: ${fileName}`);
      return outputPath;
    } catch (error) {
      logger.error('Error downloading video:', error);
      throw new Error('Failed to download video');
    }
  }

  async deleteLocalFile(filePath: string): Promise<void> {
    try {
      await fs.unlink(filePath);
      logger.info(`Local file deleted: ${filePath}`);
    } catch (error) {
      logger.error('Error deleting local file:', error);
    }
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
}

export default new YouTubeService();
