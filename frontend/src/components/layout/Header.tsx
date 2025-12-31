import Link from 'next/link';
import { Newspaper, Settings, Search } from 'lucide-react';
import styles from './Header.module.css';

export default function Header() {
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
            <input type="text" placeholder="ニュースを検索..." className={styles.searchInput} />
          </div>
          <Link href="/settings" className={styles.settingsBtn}>
            <Settings size={20} />
          </Link>
        </nav>
      </div>
    </header>
  );
}
