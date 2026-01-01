import { Video } from '@/types/news';
import { X, ExternalLink, Calendar } from 'lucide-react';
import styles from './DetailModal.module.css';
import { motion, AnimatePresence } from 'framer-motion';

interface DetailModalProps {
  video: Video | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function DetailModal({ video, isOpen, onClose }: DetailModalProps) {
  if (!video) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className={styles.overlay} onClick={onClose}>
          <motion.div
            className={`glass ${styles.modal}`}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
          >
            <button className={styles.closeBtn} onClick={onClose}>
              <X size={24} />
            </button>

            <div className={styles.scrollContent}>
              <div className={styles.details}>
                {/* AI 要約セクションを最上部へ */}
                <div className={styles.headerArea}>
                    <div className={styles.meta}>
                    <span className={styles.date}>
                        <Calendar size={16} />
                        {new Date(video.published_at).toLocaleString('ja-JP')}
                    </span>
                    <span className={styles.aiTag}>AI Generated Summary</span>
                    </div>
                    <h2 className={styles.title}>{video.title}</h2>
                </div>

                <div className={styles.section}>
                  <div className={styles.summaryBox}>
                    <p className={styles.summaryText}>
                      {video.summary || "現在AIが要約を生成しています。しばらくお待ちください。"}
                    </p>
                  </div>
                </div>

                {video.key_points && video.key_points.length > 0 && (
                  <div className={styles.section}>
                    <h3 className={styles.sectionTitle}>
                      <span className={styles.indicator} />
                      重要ポイントのまとめ
                    </h3>
                    <ul className={styles.pointsList}>
                      {video.key_points.map((point) => (
                        <li key={point.id} className={styles.pointItem}>
                          {point.point}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 動画セクションを「ソース」として下部へ */}
                <div className={styles.sourceSection}>
                    <h3 className={styles.sectionTitle}>
                        <span className={styles.indicator} />
                        ソース動画を確認
                    </h3>
                    <div className={styles.videoWrapper}>
                        <iframe
                        src={`https://www.youtube.com/embed/${video.youtube_id}`}
                        title={video.title}
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                        ></iframe>
                    </div>
                    <div className={styles.sourceFooter}>
                        <a
                            href={`https://www.youtube.com/watch?v=${video.youtube_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.youtubeLink}
                        >
                            YouTubeで元動画を開く <ExternalLink size={14} />
                        </a>
                    </div>
                </div>

                <div className={styles.footer}>
                  <p className={styles.note}>
                    ※この要約はAIによって自動生成されたものです。正確な情報は動画本編をご確認ください。
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
