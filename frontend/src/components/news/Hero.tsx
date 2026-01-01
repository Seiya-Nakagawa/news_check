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
      <div className={styles.content}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={styles.textContainer}
        >
          <div className={styles.badges}>
            <span className={styles.badge}>最新ニュース</span>
          </div>
          <h1 className={styles.title}>{video.title}</h1>

          <div className={styles.summaryContainer}>
            <p className={styles.description}>
              {video.summary || "AIが内容を分析中..."}
            </p>

            {video.key_points && video.key_points.length > 0 && (
              <div className={styles.pointsWrapper}>
                <h3 className={styles.pointsSubTitle}>ニュースまとめ</h3>
                <ul className={styles.keyPointsList}>
                  {video.key_points.map((kp) => (
                    <li key={kp.id} className={styles.keyPoint}>
                      <span className={styles.pointIndicator} />
                      {kp.point}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className={styles.actions}>
            <a
              href={`https://www.youtube.com/watch?v=${video.youtube_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.videoLink}
              onClick={(e) => e.stopPropagation()}
            >
              <Play size={16} /> 動画を再生
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
