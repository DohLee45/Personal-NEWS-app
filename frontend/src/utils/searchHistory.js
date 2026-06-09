const KEY = 'pn_search_history'
const MAX = 10

export function loadSearchHistory() {
  try {
    return (JSON.parse(localStorage.getItem(KEY) || '[]'))
      .map(h => (typeof h === 'string' ? { q: h, at: '' } : h))
  } catch { return [] }
}

export function saveSearchHistory(list) {
  try { localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX))) } catch {}
}

export function addSearch(query) {
  const item = { q: query, at: new Date().toISOString() }
  const list = loadSearchHistory().filter(h => h.q !== query)
  list.unshift(item)
  saveSearchHistory(list)
}

export function clearSearchHistory() {
  try { localStorage.removeItem(KEY) } catch {}
}
