'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Newspaper, Search } from 'lucide-react';
import styles from './Header.module.css';

function HeaderContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get('q');

  const [inputValue, setInputValue] = useState(query || '');
  const [prevQuery, setPrevQuery] = useState(query);

  // URLのクエリが変わった場合に、入力欄を同期させる（Reactの推奨パターン）
  if (query !== prevQuery) {
    setPrevQuery(query);
    setInputValue(query || '');
  }

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      router.push(`/?q=${encodeURIComponent(inputValue.trim())}`);
    } else {
      router.push('/');
    }
  };

  const handleLogoClick = () => {
    setInputValue('');
  };

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo} onClick={handleLogoClick}>
          <Newspaper className={styles.icon} />
          <span className="text-gradient">News Check</span>
        </Link>

        <nav className={styles.nav}>
          <form className={styles.searchBar} onSubmit={handleSearchSubmit}>
            <input
              type="text"
              placeholder="ニュースを検索..."
              className={styles.searchInput}
              value={inputValue}
              onChange={handleSearchChange}
            />
            <button type="submit" className={styles.searchButton} aria-label="Search">
              <Search size={18} />
            </button>
          </form>
        </nav>
      </div>
    </header>
  );
}

export default function Header() {
  return (
    <Suspense fallback={<header className={styles.header}></header>}>
      <HeaderContent />
    </Suspense>
  );
}
