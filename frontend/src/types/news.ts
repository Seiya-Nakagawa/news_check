export interface KeyPoint {
  id: number;
  youtube_id: string;
  point: string;
}

export interface Video {
  youtube_id: string;
  title: string;
  channel_id: string;
  transcript?: string;
  summary?: string;
  thumbnail_url?: string;
  published_at: string;
  status: 'unprocessed' | 'processed' | 'error';
  created_at: string;
  key_points?: KeyPoint[];
}

export interface Channel {
  channel_id: string;
  name: string;
  url: string;
}

export interface DailyDigestHeadline {
  title: string;
  summary: string;
  link: string;
  source: string;
  published_at: string | null;
}

export interface DailyDigest {
  date: string;
  headlines: DailyDigestHeadline[];
  updated_at?: string;
  message?: string;
}
