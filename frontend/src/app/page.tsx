'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
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

function NewsContent() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const searchParams = useSearchParams();
  const router = useRouter();
  const searchQuery = searchParams.get('q') || '';

  const fetchVideos = async () => {
    try {
      setIsLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/news/list`);
      if (!response.ok) throw new Error('Failed to fetch videos');
      const data: ApiVideo[] = await response.json();

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
  }, []);

  const filteredVideos = videos.filter(video => {
    if (video.status !== 'processed') return false;

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

  const clearSearch = () => {
    router.push('/');
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
          {!searchQuery && <Hero video={filteredVideos[0]} onClick={handleVideoClick} />}

          <section className={`${styles.feedSection} ${searchQuery ? styles.searchActive : ''}`}>
            <div className={styles.backgroundGlowBottom} />
            <div className={styles.container}>
              <div className={styles.feedHeader}>
                <h2 className={styles.feedTitle}>
                  {searchQuery ? `"${searchQuery}" の検索結果` : '過去のニュースフィード'}
                </h2>
              </div>

              <div className={styles.grid}>
                {(searchQuery ? filteredVideos : filteredVideos.slice(1)).map((video) => (
                  <NewsCard
                    key={video.youtube_id}
                    video={video}
                    onClick={handleVideoClick}
                  />
                ))}
              </div>

              {searchQuery && (
                <div className={styles.searchFooter}>
                  <button onClick={clearSearch} className={styles.backToTopBtn}>
                    トップに戻る
                  </button>
                </div>
              )}
            </div>
          </section>
        </>
      ) : (
        <div className={styles.emptyContainer}>
          <p>{searchQuery ? `"${searchQuery}" に一致するニュースはありません。` : 'ニュースが見つかりませんでした。'}</p>
          <button onClick={searchQuery ? clearSearch : fetchVideos} className={styles.refreshBtn}>
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

export default function Home() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <NewsContent />
    </Suspense>
  );
}
