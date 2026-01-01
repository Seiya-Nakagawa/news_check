'use client';

import { useState, useEffect } from 'react';
import Hero from '@/components/news/Hero';
import NewsCard from '@/components/news/NewsCard';
import DetailModal from '@/components/news/DetailModal';
import { Video } from '@/types/news';
import styles from './page.module.css';

interface ApiVideo {
  youtube_id: string;
  title: string;
  summary?: string;
  published_at: string;
  status: 'unprocessed' | 'processed' | 'failed_transcript';
  key_points?: string[] | { point: string }[];
}

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchVideos = async () => {
    try {
      setIsLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/news/list`);
      if (!response.ok) throw new Error('Failed to fetch videos');
      const data: ApiVideo[] = await response.json();

      // APIのレスポンス形式を型のVideoに変換
      const formattedVideos: Video[] = data.map((v: ApiVideo) => ({
        youtube_id: v.youtube_id,
        title: v.title,
        channel_id: '',
        published_at: v.published_at,
        status: v.status === 'failed_transcript' ? 'error' : v.status,
        created_at: v.published_at,
        summary: v.summary,
        key_points: v.key_points ? (v.key_points as any).map((kp: string | { point: string }, idx: number) => ({
            id: idx,
            youtube_id: v.youtube_id,
            point: typeof kp === 'string' ? kp : kp.point
        })) : []
      }));

      setVideos(formattedVideos);
    } catch (error) {
      console.error('Error fetching videos:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();

    // Headerコンポーネントからの検索イベントをリッスン
    const handleSearch = (e: Event) => {
      const customEvent = e as CustomEvent<string>;
      setSearchQuery(customEvent.detail || '');
    };
    window.addEventListener('app-search', handleSearch);
    return () => window.removeEventListener('app-search', handleSearch);
  }, []);

  const filteredVideos = videos.filter(video => {
    const query = searchQuery.toLowerCase();
    return (
      video.title.toLowerCase().includes(query) ||
      (video.summary && video.summary.toLowerCase().includes(query)) ||
      (video.key_points && video.key_points.some(kp => kp.point.toLowerCase().includes(query)))
    );
  });

  const handleVideoClick = (video: Video) => {
    setSelectedVideo(video);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingContainer}>
          <div className={styles.loader}></div>
          <p>ニュースを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.backgroundGlow} />

      {filteredVideos.length > 0 ? (
        <>
          <Hero video={filteredVideos[0]} onClick={handleVideoClick} />

          <section className={styles.feedSection}>
            <div className={styles.backgroundGlowBottom} />
            <div className={styles.container}>
              <div className={styles.feedHeader}>
                <h2 className={styles.feedTitle}>
                  {searchQuery ? `"${searchQuery}" の検索結果` : '最新のニュースフィード'}
                </h2>
              </div>

              <div className={styles.grid}>
                {filteredVideos.slice(1).map((video) => (
                  <NewsCard
                    key={video.youtube_id}
                    video={video}
                    onClick={handleVideoClick}
                  />
                ))}
              </div>
            </div>
          </section>
        </>
      ) : (
        <div className={styles.emptyContainer}>
          <p>{searchQuery ? `"${searchQuery}" に一致するニュースはありません。` : 'ニュースが見つかりませんでした。'}</p>
          <button onClick={() => searchQuery ? setSearchQuery('') : fetchVideos()} className={styles.refreshBtn}>
            {searchQuery ? '検索をクリア' : '再読み込み'}
          </button>
        </div>
      )}

      <DetailModal
        video={selectedVideo}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}
