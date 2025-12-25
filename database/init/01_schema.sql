-- チャンネル情報
CREATE TABLE IF NOT EXISTS channels (
    channel_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(255)
);

-- 動画情報
CREATE TABLE IF NOT EXISTS videos (
    youtube_id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    channel_id VARCHAR(255) REFERENCES channels(channel_id),
    transcript TEXT,
    summary TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'unprocessed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 重要点 (要約のポイント)
CREATE TABLE IF NOT EXISTS key_points (
    id SERIAL PRIMARY KEY,
    youtube_id VARCHAR(255) REFERENCES videos(youtube_id) ON DELETE CASCADE,
    point TEXT NOT NULL
);

-- インデックス (検索高速化)
CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
