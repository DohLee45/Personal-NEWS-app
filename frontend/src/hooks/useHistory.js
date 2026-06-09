import { useState, useCallback } from 'react'

const STORAGE_KEY = 'pn_history'
const MAX_HISTORY = 100

function load() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}
function persist(items) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(items)) } catch {}
}

export function useHistory() {
  const [history, setHistory] = useState(load)

  const _set = useCallback((nextFn) => {
    setHistory(prev => {
      const next = typeof nextFn === 'function' ? nextFn(prev) : nextFn
      persist(next)
      return next
    })
  }, [])

  const addStage1 = useCallback((article) => {
    _set(prev => {
      const entry = {
        ...article,
        clickedAt: new Date().toISOString(),
        _stage: 1,
      }
      const filtered = prev.filter(h => h.id !== article.id)
      return [entry, ...filtered].slice(0, MAX_HISTORY)
    })
  }, [_set])

  const updateStage2 = useCallback((id, patch) => {
    _set(prev =>
      prev.map(h =>
        h.id === id
          ? { ...h, ...patch, _stage: 2, stage2Updated: true }
          : h
      )
    )
  }, [_set])

  const clearHistory = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setHistory([])
  }, [])

  return { history, addStage1, updateStage2, clearHistory }
}
