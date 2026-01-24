'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { DailyDigest } from '@/types/news';
import styles from './page.module.css';

function NewsContent() {
  const [digest, setDigest] = useState<DailyDigest | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const searchParams = useSearchParams();
  const router = useRouter();

  // URLクエリパラメータから日付を取得 (YYYY-MM-DD)
  const dateParam = searchParams.get('date');

  const fetchDailyDigest = async (targetDate?: string) => {
    try {
      setIsLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

      let url = `${apiUrl}/api/news/daily`;
      if (targetDate) {
        url += `?target_date=${targetDate}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch daily digest');
      const data: DailyDigest = await response.json();

      setDigest(data);
    } catch (error) {
      console.error('Error fetching digest:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDailyDigest(dateParam || undefined);
  }, [dateParam]);

  const formatDate = (dateString: string) => {
    try {
      const d = new Date(dateString);
      return d.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      });
    } catch {
      return dateString;
    }
  };

  const handleDateChange = (days: number) => {
    const current = digest?.date ? new Date(digest.date) : new Date();
    current.setDate(current.getDate() + days);
    const nextDate = current.toISOString().split('T')[0];
    router.push(`/?date=${nextDate}`);
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingContainer}>
          <div className={styles.loader}></div>
          <p className={styles.loadingText}>ニュースを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.backgroundGlow} />

      <div className={styles.container}>
        <header className={styles.header}>
          <button onClick={() => handleDateChange(-1)} className={styles.navButton}>
            ← 前の日
          </button>
          <div className={styles.dateDisplay}>
            <h1>{digest ? formatDate(digest.date) : '...'}</h1>
            <p className={styles.subTitle}>Daily AI News Digest</p>
          </div>
          <button onClick={() => handleDateChange(1)} className={styles.navButton}>
            次の日 →
          </button>
        </header>

        <main className={styles.mainContent}>
          {!digest?.headlines || digest.headlines.length === 0 ? (
            <div className={styles.emptyState}>
              <p>この日のニュース要約はありません。</p>
              <button onClick={() => fetchDailyDigest(dateParam || undefined)} className={styles.refreshBtn}>
                再読み込み
              </button>
            </div>
          ) : (
            <div className={styles.newsList}>
              {digest.headlines.map((item, index) => (
                <article key={index} className={styles.newsItem}>
                  <div className={styles.newsHeader}>
                    <span className={styles.bulletPoint}>●</span>
                    <h2 className={styles.newsTitle}>
                      <a href={item.link} target="_blank" rel="noopener noreferrer">
                        {item.title}
                      </a>
                    </h2>
                    <span className={styles.sourceTag}>{item.source}</span>
                  </div>
                  <p className={styles.newsSummary}>{item.summary}</p>
                </article>
              ))}
            </div>
          )}
        </main>

        <footer className={styles.footer}>
          <p>Powered by Google Gemini & Google News</p>
        </footer>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className={styles.page}>Loading...</div>}>
      <NewsContent />
    </Suspense>
  );
}
