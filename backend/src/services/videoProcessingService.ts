import { exec } from 'child_process';
import { promisify } from 'util';
import logger from '../utils/logger';

const execAsync = promisify(exec);

export class VideoProcessingService {
  async convertToMp4(inputPath: string, outputPath: string): Promise<void> {
    try {
      // Use ffmpeg to ensure proper mp4 format with h264 codec
      const command = `ffmpeg -i "${inputPath}" -c:v libx264 -c:a aac -movflags +faststart "${outputPath}"`;

      logger.info(`Converting video: ${inputPath} -> ${outputPath}`);
      await execAsync(command);

      logger.info(`Video conversion completed: ${outputPath}`);
    } catch (error) {
      logger.error('Error converting video:', error);
      throw new Error('Failed to convert video');
    }
  }

  async getVideoMetadata(filePath: string): Promise<any> {
    try {
      const command = `ffprobe -v quiet -print_format json -show_format -show_streams "${filePath}"`;
      const { stdout } = await execAsync(command);
      return JSON.parse(stdout);
    } catch (error) {
      logger.error('Error getting video metadata:', error);
      throw new Error('Failed to get video metadata');
    }
  }

  async optimizeVideo(inputPath: string, outputPath: string): Promise<void> {
    try {
      // Optimize for web playback
      const command = `ffmpeg -i "${inputPath}" -vcodec h264 -acodec aac -movflags +faststart -preset fast "${outputPath}"`;

      logger.info(`Optimizing video: ${inputPath}`);
      await execAsync(command);

      logger.info(`Video optimization completed: ${outputPath}`);
    } catch (error) {
      logger.error('Error optimizing video:', error);
      throw new Error('Failed to optimize video');
    }
  }
}

export default new VideoProcessingService();
