'use client';

import { useState, useEffect } from 'react';
import Hero from '@/components/news/Hero';
import NewsCard from '@/components/news/NewsCard';
import DetailModal from '@/components/news/DetailModal';
import { Video } from '@/types/news';
import styles from './page.module.css';

// Mock data for initial development
const MOCK_VIDEOS: Video[] = [
  {
    youtube_id: 'N138e_o11zQ',
    title: '【ライブ】最新ニュース | ANNニュース',
    channel_id: 'UC36gH3_6X-g',
    published_at: new Date().toISOString(),
    status: 'processed',
    created_at: new Date().toISOString(),
    summary: '本日の主要ニュースをAIが要約。能登半島の復旧状況や、年末年始の交通機関の混雑状況について詳しく解説しています。',
    key_points: [
      { id: 1, youtube_id: 'N138e_o11zQ', point: '能登半島の復旧作業が加速' },
      { id: 2, youtube_id: 'N138e_o11zQ', point: '年末年始の帰省ラッシュがピーク' },
      { id: 3, youtube_id: 'N138e_o11zQ', point: '全国的な寒波への警戒呼びかけ' }
    ]
  },
  {
    youtube_id: 'jNQXAC9IVRw',
    title: '全国の天気予報と気温の変化',
    channel_id: 'UC36gH3_6X-g',
    published_at: new Date(Date.now() - 3600000).toISOString(),
    status: 'processed',
    created_at: new Date().toISOString(),
    key_points: [
      { id: 4, youtube_id: 'jNQXAC9IVRw', point: '明日は全国的に晴天' },
      { id: 5, youtube_id: 'jNQXAC9IVRw', point: '乾燥注意報が各地で発令' }
    ]
  },
  {
    youtube_id: 'L-1WvEx08sc',
    title: '経済ニュース：円安の影響と株価推移',
    channel_id: 'UC36gH3_6X-g',
    published_at: new Date(Date.now() - 7200000).toISOString(),
    status: 'unprocessed',
    created_at: new Date().toISOString(),
  }
];

export default function Home() {
  const [videos] = useState<Video[]>(MOCK_VIDEOS);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    // In a real app, we would fetch from the API here
    // setVideos(MOCK_VIDEOS);
  }, []);

  const handleVideoClick = (video: Video) => {
    setSelectedVideo(video);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <div className={styles.page}>
      <div className={styles.backgroundGlow} />

      {videos.length > 0 && (
        <Hero video={videos[0]} onClick={handleVideoClick} />
      )}

      <section className={styles.feedSection}>
        <div className={styles.backgroundGlowBottom} />
        <div className={styles.container}>
          <div className={styles.feedHeader}>
            <h2 className={styles.feedTitle}>最新のニュースフィード</h2>
            <div className={styles.filters}>
              <button className={`${styles.filterBtn} ${styles.active}`}>すべて</button>
              <button className={styles.filterBtn}>今日</button>
              <button className={styles.filterBtn}>今週</button>
            </div>
          </div>

          <div className={styles.grid}>
            {videos.slice(1).map((video) => (
              <NewsCard
                key={video.youtube_id}
                video={video}
                onClick={handleVideoClick}
              />
            ))}
          </div>
        </div>
      </section>

      <DetailModal
        video={selectedVideo}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}
