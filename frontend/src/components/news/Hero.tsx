import { Video } from '@/types/news';
import { Play } from 'lucide-react';
import styles from './Hero.module.css';
import { motion } from 'framer-motion';
import Image from 'next/image';

interface HeroProps {
  video: Video;
  onClick: (video: Video) => void;
}

export default function Hero({ video, onClick }: HeroProps) {
  const thumbnailUrl = `https://img.youtube.com/vi/${video.youtube_id}/maxresdefault.jpg`;

  return (
    <section className={styles.hero} onClick={() => onClick(video)}>
      <div className={styles.background}>
        <Image
          src={thumbnailUrl}
          alt={video.title}
          className={styles.bgImage}
          fill
          priority
          sizes="100vw"
          onError={(e) => {
            // maxresdefault がない場合のフォールバック
            const target = e.target as HTMLImageElement;
            target.src = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;
          }}
        />
        <div className={styles.overlay} />
      </div>

      <div className={styles.content}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={styles.textContainer}
        >
          <div className={styles.badges}>
            <span className={styles.badge}>Breaking News</span>
            <span className={styles.aiBadge}>AI Analyzed</span>
          </div>
          <h1 className={styles.title}>{video.title}</h1>

          <div className={styles.summaryContainer}>
            <p className={styles.description}>
              {video.summary || "AIが内容を分析中..."}
            </p>

            {video.key_points && video.key_points.length > 0 && (
              <ul className={styles.keyPointsList}>
                {video.key_points.slice(0, 3).map((kp) => (
                  <li key={kp.id} className={styles.keyPoint}>
                    <span className={styles.pointIndicator} />
                    {kp.point}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className={styles.actions}>
            <button className={styles.primaryBtn}>
                AI要約を詳しく読む
            </button>
            <div className={styles.videoLink}>
              <Play size={16} /> 動画を再生
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
