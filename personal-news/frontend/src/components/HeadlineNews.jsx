import { memo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './HeadlineNews.module.css'
import { stripHtml, relativeTime } from '../utils/formatUtils'

const HeadlineNews = memo(function HeadlineNews({ article, onRead }) {
  const navigate = useNavigate()

  const handleClick = useCallback(() => {
    if (onRead) onRead(article)
    navigate(`/article/${article.id}`, { state: { article } })
  }, [article, onRead, navigate])

  if (!article) return null

  return (
    <article
      className={styles.card}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && handleClick()}
      aria-label={`헤드라인: ${article.title}`}
    >
      <div className={styles.meta}>
        <span className={styles.label}>헤드라인</span>
        {article.category && (
          <span className={styles.category}>{article.category}</span>
        )}
        <span className={styles.time}>{relativeTime(article.published)}</span>
      </div>

      <h2 className={styles.title}>{article.title}</h2>

      {article.summary && (
        <p className={styles.summary}>{stripHtml(article.summary)}</p>
      )}

      <div className={styles.footer}>
        <span className={styles.source}>{article.source}</span>
      </div>
    </article>
  )
})

export default HeadlineNews
