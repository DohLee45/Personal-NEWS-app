import { memo, useState, useRef, useCallback, useEffect } from 'react'
import styles from './SearchBar.module.css'
import { loadSearchHistory, addSearch } from '../utils/searchHistory'

const SearchBar = memo(function SearchBar({ onInstantSearch, onSearch }) {
  const [value,   setValue]   = useState('')
  const [open,    setOpen]    = useState(false)
  const [history, setHistory] = useState(loadSearchHistory)
  const debounceRef = useRef(null)
  const wrapRef     = useRef(null)

  useEffect(() => {
    function handler(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const persistHistory = useCallback((q) => {
    addSearch(q)
    setHistory(loadSearchHistory())
  }, [])

  const submitRSS = useCallback((q) => {
    const trimmed = q.trim()
    if (!trimmed) return
    onSearch(trimmed)
    setOpen(false)
  }, [onSearch])

  function handleChange(e) {
    const v = e.target.value
    setValue(v)
    setOpen(!v && history.length > 0)
    onInstantSearch(v.trim())
    clearTimeout(debounceRef.current)
    if (v.trim()) {
      debounceRef.current = setTimeout(() => submitRSS(v), 300)
    } else {
      onSearch('')
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      clearTimeout(debounceRef.current)
      const trimmed = value.trim()
      if (trimmed) persistHistory(trimmed)
      submitRSS(value)
    }
    if (e.key === 'Escape') { setOpen(false) }
  }

  function handleFocus() {
    if (!value && history.length > 0) setOpen(true)
  }

  function handleClear() {
    setValue('')
    onInstantSearch('')
    onSearch('')
    setOpen(history.length > 0)
  }

  function handleHistoryClick(q) {
    setValue(q)
    onInstantSearch(q)
    submitRSS(q)
  }

  return (
    <div className={styles.wrap} ref={wrapRef}>
      <input
        type="search"
        className={styles.input}
        placeholder="키워드 검색…"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        autoComplete="off"
        aria-label="뉴스 검색"
      />
      {value && (
        <button className={styles.clearBtn} onClick={handleClear} aria-label="검색어 지우기">
          ✕
        </button>
      )}
      {open && history.length > 0 && (
        <div className={styles.dropdown} role="listbox" aria-label="최근 검색어">
          {history.map(h => (
            <button
              key={h.q}
              className={styles.dropItem}
              role="option"
              onClick={() => handleHistoryClick(h.q)}
            >
              <span className={styles.dropIcon}>🕒</span>
              {h.q}
            </button>
          ))}
        </div>
      )}
    </div>
  )
})

export default SearchBar
