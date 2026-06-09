import { useState, useEffect, useRef, useCallback } from 'react'
import { sortByInterest } from '../utils/interestScore'

const _cache = new Map()
const CACHE_TTL = 5 * 60 * 1000

function cacheKey(q) {
  return q ? `search|${q}` : '__feed__'
}

async function fetchArticles(kws, q, signal) {
  if (q) {
    const res = await fetch(
      `/api/news?keywords=${encodeURIComponent(q)}&max=40&when=20d`,
      { signal }
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
  const res = await fetch(`/api/news?max=20`, { signal })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function useFeed(keywords, search = '', history = []) {
  const key = cacheKey(search)

  const cached = _cache.get(key)
  const isFresh = cached && (Date.now() - cached.ts < CACHE_TTL)

  const [articles,  setArticles]  = useState(
    cached?.articles ? sortByInterest(cached.articles, keywords, history) : []
  )
  const [isLoading, setIsLoading] = useState(!isFresh)
  const [isStale,   setIsStale]   = useState(!!cached && !isFresh)
  const [error,     setError]     = useState(null)

  const abortRef = useRef(null)
  const keyRef   = useRef(key)

  const runFetch = useCallback(async (kws, q, hist) => {
    const thisKey = cacheKey(q)

    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    const staleEntry = _cache.get(thisKey)
    if (staleEntry) {
      setArticles(sortByInterest(staleEntry.articles, kws, hist))
      setIsStale(true)
    }

    setIsLoading(true)
    setError(null)

    try {
      const raw = await fetchArticles(kws, q, ctrl.signal)
      if (keyRef.current !== thisKey) return

      const sorted = sortByInterest(raw, kws, hist)
      _cache.set(thisKey, { articles: raw, ts: Date.now() })

      setArticles(sorted)
      setIsStale(false)
    } catch (err) {
      if (err.name === 'AbortError') return
      setError(err.message || '뉴스를 불러오지 못했습니다.')
    } finally {
      if (keyRef.current === thisKey) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    keyRef.current = key

    if (isFresh && cached) {
      setArticles(sortByInterest(cached.articles, keywords, history))
      setIsLoading(false)
      setIsStale(false)
      return
    }

    runFetch(keywords, search, history)
    return () => { if (abortRef.current) abortRef.current.abort() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  useEffect(() => {
    const entry = _cache.get(key)
    if (entry) {
      setArticles(sortByInterest(entry.articles, keywords, history))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(keywords)])

  const refresh = useCallback(() => {
    _cache.delete(key)
    runFetch(keywords, search, history)
  }, [key, keywords, search, history, runFetch])

  return { articles, isLoading, isStale, error, refresh }
}
