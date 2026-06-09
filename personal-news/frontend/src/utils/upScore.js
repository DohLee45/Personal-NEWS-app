import { getMediaLean } from './mediaBias'

const W = { opinion: 0.35, source: 0.25, bimodal: 0.25, intensity: 0.15 }
const HALFLIFE_DAYS = 7

const clamp01 = v => Math.max(0, Math.min(1, v))

function tWeight(clickedAt) {
  if (!clickedAt) return 1
  const days = (Date.now() - new Date(clickedAt).getTime()) / 86_400_000
  return Math.exp(-0.693 * days / HALFLIFE_DAYS)
}

function calcOpinion(arts) {
  let sumV = 0, sumW = 0, neutCnt = 0
  for (const a of arts) {
    const w = tWeight(a.clickedAt)
    const s = a.biasScore ?? 0
    if      (a.viewpoint === 'pro') { sumV += s * w }
    else if (a.viewpoint === 'con') { sumV -= s * w }
    else                            { neutCnt++ }
    sumW += w
  }
  const wm = sumW > 0 ? sumV / sumW : 0
  const nr = neutCnt / arts.length
  return clamp01(Math.abs(wm) * (1 - nr * 0.2))
}

function leanGroup(source) {
  const lean = getMediaLean(source)
  if (lean === 'conservative' || lean === 'moderate_right') return 'cons'
  if (lean === 'progressive'  || lean === 'moderate_left')  return 'prog'
  return 'neut'
}

function calcSource(arts) {
  let c = 0, p = 0, n = 0
  for (const a of arts) {
    const g = leanGroup(a.source)
    if      (g === 'cons') c++
    else if (g === 'prog') p++
    else                   n++
  }
  const t = arts.length
  return clamp01(Math.abs(c / t - p / t) * (1 - (n / t) * 0.3))
}

function calcBimodal(arts) {
  let pro = 0, con = 0, neut = 0
  const vals = []
  for (const a of arts) {
    const s = a.biasScore ?? 0
    if      (a.viewpoint === 'pro') { pro++;  vals.push( s) }
    else if (a.viewpoint === 'con') { con++;  vals.push(-s) }
    else                            { neut++; vals.push(0)  }
  }
  const t  = arts.length
  const pr = pro / t, cr = con / t, nr = neut / t
  const unimod = Math.abs(pr - cr)
  const minor  = Math.min(pr, cr)
  const bimod  = minor > 0.1 ? minor * (1 - nr) : 0
  const mean  = vals.reduce((s, v) => s + v, 0) / t
  const std   = Math.sqrt(vals.reduce((s, v) => s + (v - mean) ** 2, 0) / t)
  const bonus = Math.min(0.2, std * 0.3)
  return clamp01(Math.max(0, Math.max(unimod, bimod) - bonus))
}

function calcIntensity(arts) {
  const ss  = arts.map(a => a.biasScore ?? 0)
  const avg = ss.reduce((s, v) => s + v, 0) / ss.length
  const hr  = ss.filter(v => v >= 0.6).length / ss.length
  return clamp01(avg * 0.6 + hr * 0.4)
}

export function calcTopicDiversity(arts) {
  if (!arts?.length) return 0
  const cnt = {}
  for (const a of arts) {
    const c = a.category || '기타'
    cnt[c] = (cnt[c] || 0) + 1
  }
  const vals = Object.values(cnt)
  const k    = vals.length
  if (k <= 1) return 0
  const n = arts.length
  let H = 0
  for (const v of vals) {
    const p = v / n
    if (p > 0) H -= p * Math.log(p)
  }
  return Math.round(clamp01(H / Math.log(k)) * 100)
}

export function buildMessages({ d_opinion, d_source, d_bimodal, d_intensity }) {
  const msgs = []
  if (d_opinion  > 0.4)                    msgs.push('다른 관점의 기사도 읽어보세요')
  if (d_source   > 0.4)                    msgs.push('다양한 언론사의 기사를 접해보세요')
  if (d_bimodal  > 0.3 && d_opinion < 0.2) msgs.push('중도·사실 보도도 함께 읽어보세요')
  if (d_intensity > 0.5)                   msgs.push('편향도 낙은 기사도 함께 읽어보세요')
  if (msgs.length === 0)                   msgs.push('균형 잊힌 뉴스를 읽고 있어요! 👍')
  return msgs
}

export function calculateUP(articles) {
  if (!articles?.length) return null
  const d_opinion   = calcOpinion(articles)
  const d_source    = calcSource(articles)
  const d_bimodal   = calcBimodal(articles)
  const d_intensity = calcIntensity(articles)
  const up          = clamp01(
    W.opinion   * d_opinion   +
    W.source    * d_source    +
    W.bimodal   * d_bimodal   +
    W.intensity * d_intensity
  )
  return {
    up,
    d_opinion, d_source, d_bimodal, d_intensity,
    diversity:    (1 - up) * 100,
    articleCount: articles.length,
  }
}
