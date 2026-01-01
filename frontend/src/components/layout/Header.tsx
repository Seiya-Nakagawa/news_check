'use client';

import Link from 'next/link';
import { Newspaper, Search } from 'lucide-react';
import styles from './Header.module.css';

export default function Header() {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const event = new CustomEvent('app-search', { detail: e.target.value });
    window.dispatchEvent(event);
  };

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo}>
          <Newspaper className={styles.icon} />
          <span className="text-gradient">News Check</span>
        </Link>

        <nav className={styles.nav}>
          <div className={styles.searchBar}>
            <Search size={18} className={styles.searchIcon} />
            <input
              type="text"
              placeholder="ニュースを検索..."
              className={styles.searchInput}
              onChange={handleSearchChange}
            />
          </div>
        </nav>
      </div>
    </header>
  );
}
