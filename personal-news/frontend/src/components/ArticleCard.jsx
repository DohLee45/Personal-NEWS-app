import { memo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './ArticleCard.module.css'
import { stripHtml, relativeTime } from '../utils/formatUtils'

const ArticleCard = memo(function ArticleCard({ article, onRead, isSearchResult = false }) {
  const navigate = useNavigate()

  const handleClick = useCallback(() => {
    if (onRead) onRead(article)
    navigate(`/article/${article.id}`, { state: { article } })
  }, [article, onRead, navigate])

  return (
    <article
      className={styles.card}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && handleClick()}
      aria-label={article.title}
    >
      <div className={styles.meta}>
        {article.category && (
          <span className={styles.category}>{article.category}</span>
        )}
        <span className={styles.time}>{relativeTime(article.published)}</span>
      </div>

      <h3 className={styles.title}>{article.title}</h3>

      {!isSearchResult && article.summary && (
        <p className={styles.summary}>{stripHtml(article.summary)}</p>
      )}

      <div className={styles.footer}>
        <span className={styles.source}>{article.source}</span>
      </div>
    </article>
  )
})

export default ArticleCard
