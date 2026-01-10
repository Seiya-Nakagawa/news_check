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
