import mongoose, { Schema, Document } from 'mongoose';
import type { DownloadJob, VideoInfo } from '../types';

export interface IDownload extends Document, Omit<DownloadJob, '_id'> {}

const VideoInfoSchema = new Schema<VideoInfo>(
  {
    id: { type: String, required: true },
    title: { type: String, required: true },
    thumbnail: { type: String, required: true },
    duration: { type: Number, required: true },
    fileSize: { type: String },
    quality: { type: String },
  },
  { _id: false }
);

const DownloadSchema = new Schema<IDownload>(
  {
    url: {
      type: String,
      required: true,
      trim: true,
    },
    jobId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    status: {
      type: String,
      enum: ['queued', 'processing', 'completed', 'failed'],
      default: 'queued',
      required: true,
    },
    progress: {
      type: Number,
      min: 0,
      max: 100,
      default: 0,
    },
    videoInfo: {
      type: VideoInfoSchema,
    },
    downloadUrl: {
      type: String,
    },
    error: {
      type: String,
    },
  },
  {
    timestamps: true,
  }
);

// Index for cleanup queries
DownloadSchema.index({ createdAt: 1 });
DownloadSchema.index({ status: 1 });

export default mongoose.model<IDownload>('Download', DownloadSchema);
