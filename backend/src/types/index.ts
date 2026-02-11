export interface VideoInfo {
  id: string;
  title: string;
  thumbnail: string;
  duration: number;
  fileSize?: string;
  quality?: string;
}

export interface DownloadJob {
  url: string;
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress?: number;
  videoInfo?: VideoInfo;
  downloadUrl?: string;
  error?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface DownloadRequest {
  url: string;
}

export interface DownloadResponse {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  videoInfo?: VideoInfo;
  downloadUrl?: string;
  error?: string;
}
