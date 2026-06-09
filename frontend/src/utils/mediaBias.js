const BIAS_MAP = {
  '조선일보': 'conservative', '조선비즈': 'conservative',
  '동아일보': 'conservative', '동아닷컴': 'conservative',
  'TV조선': 'conservative',  '채널A': 'conservative',
  'MBN': 'conservative',     '문화일보': 'conservative',
  '중앙일보': 'moderate_right', 'JoongAng': 'moderate_right',
  '매일경제': 'moderate_right', 'MK': 'moderate_right',
  '한국경제': 'moderate_right', '서울경제': 'moderate_right',
  '이데일리': 'moderate_right',
  'KBS': 'neutral', '연합뉴스': 'neutral', '뉴시스': 'neutral',
  '뉴스리': 'neutral', 'YTN': 'neutral', 'SBS': 'neutral',
  '아이뉴스24': 'neutral', 'ZDNet': 'neutral', '디지털타임스': 'neutral',
  'MBC': 'moderate_left', 'JTBC': 'moderate_left',
  '한국일보': 'moderate_left', '시사IN': 'moderate_left',
  '머니투데이': 'moderate_left',
  '한거레': 'progressive', '경향신문': 'progressive',
  '오마이뉴스': 'progressive', '프레시안': 'progressive',
  '민중의소리': 'progressive',
}

export const LEAN_GROUP_COLORS = {
  cons: '#e74c3c',
  neut: '#27ae60',
  prog: '#3498db',
}

export function getMediaLean(source) {
  if (!source) return null
  for (const [media, lean] of Object.entries(BIAS_MAP)) {
    if (source.includes(media)) return lean
  }
  return null
}
