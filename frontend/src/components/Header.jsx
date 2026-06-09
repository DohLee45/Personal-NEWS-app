import { memo, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import SearchBar from './SearchBar'
import styles from './Header.module.css'

const WEEKDAYS = ['일','월','화','수','목','금','토']

function formatDate(d) {
  const yy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const day = WEEKDAYS[d.getDay()]
  return `${yy}.${mm}.${dd}(${day})`
}

const Header = memo(function Header({ onSearch, onInstantSearch }) {
  const navigate = useNavigate()
  const nickname = localStorage.getItem('pn_nickname') || '사용자'
  const dateStr  = useMemo(() => formatDate(new Date()), [])

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div
          className={styles.brand}
          role="button"
          tabIndex={0}
          onClick={() => navigate('/')}
          onKeyDown={e => e.key === 'Enter' && navigate('/')}
          aria-label="홈으로 이동"
        >
          <span className={styles.logo}>Personal NEWS</span>
          <span className={styles.sub}>{nickname}님의 뉴스룸 · {dateStr}</span>
        </div>
        <div className={styles.spacer} />
        <div className={styles.searchWrap}>
          <SearchBar
            onSearch={onSearch ?? (() => {})}
            onInstantSearch={onInstantSearch ?? (() => {})}
          />
        </div>
        <nav className={styles.actions} aria-label="메뉴">
          <button
            className={styles.iconBtn}
            title="편향 분석"
            aria-label="편향 분석 페이지"
            onClick={() => navigate('/analysis')}
          >
            📊
          </button>
          <button
            className={styles.iconBtn}
            title="설정"
            aria-label="설정 페이지"
            onClick={() => navigate('/settings')}
          >
            ⚙️
          </button>
        </nav>
      </div>
      <div className={styles.line} />
    </header>
  )
})

export default Header
