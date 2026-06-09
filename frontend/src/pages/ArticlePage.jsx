import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import Header from '../components/Header'
import { useHistory } from '../hooks/useHistory'
import { API_BASE } from '../utils/apiBase'
import styles from './ArticlePage.module.css'

function biasColor(score) {
  if (score < 0.30) return 'green'
  if (score < 0.60) return 'yellow'
  return 'red'
}

function BiasBar({ score, tag }) {
  const color = biasColor(score)
  const pct   = Math.round(score * 100)
  return (
    <div className={styles.biasRow}>
      <span className={styles.biasLabel}>편향도</span>
      <div className={styles.biasBarWrap}>
        <div
          className={`${styles.biasBarFill} ${styles[color]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={styles.biasTag}>{tag}</span>
      <span className={styles.biasScore}>{pct}%</span>
    </div>
  )
}

export default function ArticlePage() {
  const navigate                              = useNavigate()
  const { id }                               = useParams()
  const { state }                            = useLocation()
  const { updateStage2, addStage1, history } = useHistory()

  const article = state?.article ?? history.find(h => h.id === id) ?? null

  const [crawlPhase,  setCrawlPhase]  = useState('loading')
  const [summary,     setSummary]     = useState('')
  const [updatedBias, setUpdatedBias] = useState(null)
  const [related, setRelated] = useState({ loading: true, articles: [] })
  const [deepPhase, setDeepPhase] = useState('idle')
  const [deepData,  setDeepData]  = useState(null)

  const didFetch = useRef(false)

  useEffect(() => {
    if (!article || didFetch.current) return
    didFetch.current = true

    const ctrl = new AbortController()

    const runAnalysis = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/analysis`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          signal:  ctrl.signal,
          body: JSON.stringify({
            url:      article.link     || '',
            title:    article.title    || '',
            source:   article.source   || '',
            category: article.category || '사회',
            summary:  article.summary  || '',
          }),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()

        setSummary(data.summary || '')
        setUpdatedBias(data.updated_bias ?? null)
        setCrawlPhase('done')

        if (data.updated_bias && article.id) {
          updateStage2(article.id, {
            biasScore: data.updated_bias.biasScore,
            biasTag:   data.updated_bias.biasTag,
            viewpoint: data.updated_bias.viewpoint,
          })
        }
      } catch (err) {
        if (err.name !== 'AbortError') setCrawlPhase('error')
      }
    }

    const runRelated = async () => {
      try {
        const params = new URLSearchParams({
          title:       article.title  || '',
          source:      article.source || '',
          exclude_url: article.link   || '',
        })
        const res = await fetch(`${API_BASE}/api/related?${params}`, { signal: ctrl.signal })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setRelated({ loading: false, articles: data.articles ?? [] })
      } catch (err) {
        if (err.name !== 'AbortError') {
          setRelated({ loading: false, articles: [] })
        }
      }
    }

    runAnalysis()
    runRelated()

    return () => ctrl.abort()
  }, [article, updateStage2])

  const handleDeepAnalysis = useCallback(async () => {
    if (deepPhase !== 'idle' || !article) return
    setDeepPhase('loading')
    try {
      const res = await fetch(`${API_BASE}/api/deep-analysis`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url:      article.link     || '',
          title:    article.title    || '',
          source:   article.source   || '',
          category: article.category || '사회',
          summary:  article.summary  || '',
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setDeepData(data)
      setDeepPhase('done')
    } catch {
      setDeepPhase('error')
    }
  }, [deepPhase, article])

  const handleRelatedClick = useCallback((a) => {
    if (!a?.id) return
    const clickArticle = {
      id:        a.id,
      title:     a.title     || '',
      link:      a.link      || '',
      source:    a.source    || '',
      category:  a.category  || '',
      biasTag:   a.biasTag   || '균형 보도',
      biasScore: typeof a.biasScore === 'number' ? a.biasScore : 0,
      viewpoint: a.viewpoint || 'neutral',
      published: a.published || '',
      summary:   a.summary   || '',
    }
    addStage1(clickArticle)
    window.location.href = '/article/' + clickArticle.id
  }, [addStage1])

  if (!article) {
    return (
      <div className={styles.page}>
        <Header />
        <div className={styles.body}>
          <button className={styles.back} onClick={() => navigate(-1)}>← 뒤로가기</button>
          <p className={styles.placeholder}>기사 정보를 불러올 수 없습니다. (ID: {id})</p>
        </div>
      </div>
    )
  }

  const displayScore = updatedBias?.biasScore ?? article.biasScore ?? 0
  const displayTag   = updatedBias?.biasTag   ?? article.biasTag   ?? ''

  return (
    <div className={styles.page}>
      <Header />
      <div className={styles.body}>
        <button className={styles.back} onClick={() => navigate(-1)}>← 뒤로가기</button>

        <div className={styles.card}>
          {article.category && (
            <span className={styles.cat}>{article.category}</span>
          )}
          <h1 className={styles.title}>{article.title}</h1>
          <p className={styles.meta}>
            {article.source}
            {article.published && ` · ${article.published.slice(0, 10)}`}
          </p>
          <BiasBar score={displayScore} tag={displayTag} />
          {article.link && (
            <a
              href={article.link}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.originalLink}
            >
              원문 기사 보기 →
            </a>
          )}
        </div>

        {crawlPhase === 'loading' && (
          <div className={styles.skeletonSection}>
            <div className={styles.skeleton} />
            <div className={`${styles.skeleton} ${styles.skeletonShort}`} />
            <div className={styles.skeleton} />
            <div className={`${styles.skeleton} ${styles.skeletonMed}`} />
            <p className={styles.skeletonHint}>원문을 불러오는 중입니다...</p>
          </div>
        )}

        {crawlPhase !== 'loading' && (
          <div className={styles.section}>
            <p className={styles.sectionTitle}>📝 원문 요약</p>
            {summary
              ? <p className={styles.analysisText}>{summary}</p>
              : <p className={styles.analysisText}>요약을 불러올 수 없습니다.</p>
            }
          </div>
        )}

        <div className={styles.relatedSection}>
          <p className={styles.relatedTitle}>👁 다른 시각 기사</p>
          {related.loading && (
            <p className={styles.loadingText}>추천 기사를 불러오는 중...</p>
          )}
          {!related.loading && related.articles.length === 0 && (
            <p className={styles.nonDebateMsg}>관련 기사를 찾지 못했습니다.</p>
          )}
          {!related.loading && related.articles.length > 0 && (
            <div className={styles.relatedList}>
              {related.articles
                .filter(a => a.link !== article.link)
                .map(a => (
                  <div
                    key={a.id ?? a.link}
                    className={styles.relatedCard}
                    onClick={() => handleRelatedClick(a)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={e => { if (e.key === 'Enter') handleRelatedClick(a) }}
                  >
                    <span className={styles.relatedCardTitle}>{a.title}</span>
                    <span className={styles.relatedCardMeta}>
                      {a.category && (
                        <span className={styles.relatedCardCat}>{a.category}</span>
                      )}
                      <span>{a.source}</span>
                      {a.biasTag && (
                        <span className={styles.relatedCardTag}>{a.biasTag}</span>
                      )}
                    </span>
                  </div>
                ))}
            </div>
          )}
        </div>

        <div className={styles.agentCWrap}>
          {deepPhase === 'idle' && (
            <>
              <button className={styles.agentCBtn} onClick={handleDeepAnalysis}>
                🔍 AI 정밀 분석
              </button>
              <p className={styles.agentCHint}>
                AI가 기사의 편향성을 정밀 분석합니다 (API 1회 소모)
              </p>
            </>
          )}
          {deepPhase === 'loading' && (
            <div className={styles.agentCLoadingBox}>
              <div className={styles.spinner} />
              <p className={styles.loadingText}>AI가 분석 중입니다...</p>
            </div>
          )}
          {deepPhase === 'error' && (
            <p className={styles.agentCUnavailable}>분석 중 오류가 발생했습니다.</p>
          )}
          {deepPhase === 'done' && deepData?.ai_unavailable && (
            <p className={styles.agentCUnavailable}>
              {deepData.message ?? 'OpenRouter API 사용량이 다 하였습니다.'}
            </p>
          )}
        </div>

        {deepPhase === 'done' && deepData && !deepData.ai_unavailable && (
          <>
            {deepData.bias_explanation && (
              <div className={styles.section}>
                <p className={styles.sectionTitle}>⚖️ 편향 판별 설명</p>
                <p className={styles.analysisText}>{deepData.bias_explanation}</p>
              </div>
            )}
            {(deepData.pro_view || deepData.con_view) && (
              <div className={styles.section}>
                <p className={styles.sectionTitle}>👥 찬반 입장</p>
                <div className={styles.proConGrid}>
                  {deepData.pro_view && (
                    <div className={styles.proBox}>
                      <p className={styles.proConLabel}>찬성 측</p>
                      <p className={styles.proConText}>{deepData.pro_view}</p>
                    </div>
                  )}
                  {deepData.con_view && (
                    <div className={styles.conBox}>
                      <p className={styles.proConLabel}>반대 측</p>
                      <p className={styles.proConText}>{deepData.con_view}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
            {deepData.neutral_view && (
              <div className={styles.section}>
                <p className={styles.sectionTitle}>⚖️ 중도 시각</p>
                <p className={styles.analysisText}>{deepData.neutral_view}</p>
              </div>
            )}
            {deepData.context_note && (
              <div className={styles.section}>
                <p className={styles.sectionTitle}>📖 맥락 정보</p>
                <p className={styles.analysisText}>{deepData.context_note}</p>
              </div>
            )}
            {typeof deepData.ai_bias_score === 'number' && deepData.ai_bias_score >= 0 && (
              <div className={styles.section}>
                <p className={styles.sectionTitle}>🔢 AI 편향도 점수</p>
                <p className={styles.analysisText}>
                  규칙 기반: {displayScore.toFixed(2)}&nbsp;|&nbsp;AI 판단: {deepData.ai_bias_score.toFixed(2)}
                </p>
              </div>
            )}
            {deepData.cross_check && (
              <div className={styles.section}>
                <p className={styles.sectionTitle}>🔍 교차검증 포인트</p>
                <p className={styles.analysisText}>{deepData.cross_check}</p>
              </div>
            )}
            {deepData.recommendations && deepData.recommendations.length > 0 && (
              <div className={styles.relatedSection}>
                <p className={styles.relatedTitle}>💡 관련 논점 기사</p>
                <div className={styles.relatedList}>
                  {deepData.recommendations.map(a => (
                    <div
                      key={a.id ?? a.link}
                      className={styles.relatedCard}
                      onClick={() => handleRelatedClick(a)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={e => { if (e.key === 'Enter') handleRelatedClick(a) }}
                    >
                      <span className={styles.relatedCardTitle}>{a.title}</span>
                      <span className={styles.relatedCardMeta}>
                        {a.category && (
                          <span className={styles.relatedCardCat}>{a.category}</span>
                        )}
                        <span>{a.source}</span>
                        {a.biasTag && (
                          <span className={styles.relatedCardTag}>{a.biasTag}</span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  )
}
