import { Video } from '@/types/news';
import { Play, ChevronRight, Clock } from 'lucide-react';
import styles from './NewsCard.module.css';
import { motion } from 'framer-motion';
import Image from 'next/image';

interface NewsCardProps {
  video: Video;
  onClick: (video: Video) => void;
}

export default function NewsCard({ video, onClick }: NewsCardProps) {
  const thumbnailUrl = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;

  return (
    <motion.div
      className={`glass-card ${styles.card}`}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <div className={styles.thumbnailWrapper} onClick={() => onClick(video)}>
        <Image
          src={thumbnailUrl}
          alt={video.title}
          className={styles.thumbnail}
          width={400}
          height={225}
        />
        <div className={styles.playOverlay}>
          <Play fill="white" size={32} />
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.meta}>
          <span className={styles.badge}>News</span>
          <span className={styles.date}>
            <Clock size={12} />
            {new Date(video.published_at).toLocaleDateString('ja-JP')}
          </span>
        </div>

        <h3 className={styles.title} onClick={() => onClick(video)}>{video.title}</h3>

        <div className={styles.summary}>
          {video.key_points && video.key_points.length > 0 ? (
            <ul className={styles.points}>
              {video.key_points.slice(0, 2).map((point, i) => (
                <li key={i}>{point.point}</li>
              ))}
            </ul>
          ) : (
            <p className={styles.placeholderSummary}>AI要約を生成中...</p>
          )}
        </div>

        <button className={styles.cta} onClick={() => onClick(video)}>
          詳細を見る <ChevronRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}
