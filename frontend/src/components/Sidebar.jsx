import { memo } from 'react'
import WeatherWidget  from './widgets/WeatherWidget'
import BreakingWidget from './widgets/BreakingWidget'
import MarketWidget   from './widgets/MarketWidget'
import RankingWidget  from './widgets/RankingWidget'
import styles from './Sidebar.module.css'

const Sidebar = memo(function Sidebar() {
  return (
    <aside className={styles.sidebar} aria-label="사이드바">
      <WeatherWidget />
      <BreakingWidget />
      <MarketWidget />
      <RankingWidget />
    </aside>
  )
})

export default Sidebar
