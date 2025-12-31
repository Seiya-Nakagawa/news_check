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
  const thumbnailUrl = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;

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
        />
        <div className={styles.overlay} />
      </div>

      <div className={styles.content}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className={styles.badge}>Breaking News</span>
          <h1 className={styles.title}>{video.title}</h1>
          <p className={styles.description}>
            {video.summary || "AIがこの動画の内容を分析し、重要な情報を抽出しました。詳細な要約を確認するにはクリックしてください。"}
          </p>

          <div className={styles.actions}>
            <button className={styles.primaryBtn}>
              <Play fill="white" size={18} /> 今すぐ見る
            </button>
            <button className={styles.secondaryBtn}>
              詳細をチェック
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
