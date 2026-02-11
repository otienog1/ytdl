import { z } from 'zod';

const YOUTUBE_SHORTS_PATTERNS = [
  /^https?:\/\/(www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})(\?.*)?$/,
  /^https?:\/\/youtu\.be\/([a-zA-Z0-9_-]{11})(\?.*)?$/,
];

export const downloadRequestSchema = z.object({
  url: z.string().url().refine((url) => {
    return YOUTUBE_SHORTS_PATTERNS.some(pattern => pattern.test(url));
  }, {
    message: 'Please provide a valid YouTube Shorts URL',
  }),
});

export function extractVideoId(url: string): string | null {
  for (const pattern of YOUTUBE_SHORTS_PATTERNS) {
    const match = url.match(pattern);
    if (match) {
      // For youtube.com/shorts/, video ID is in match[2] (after optional www. in match[1])
      // For youtu.be/, video ID is in match[1]
      return match[2] || match[1];
    }
  }
  return null;
}

export function isValidYouTubeShortsUrl(url: string): boolean {
  try {
    downloadRequestSchema.parse({ url });
    return true;
  } catch {
    return false;
  }
}
