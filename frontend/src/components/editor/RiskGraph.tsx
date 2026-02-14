import './RiskGraph.css'

interface RiskPoint {
  timestamp: number
  riskLevel: number
}

interface RiskGraphProps {
  riskData: RiskPoint[]
  currentTime: number
  duration?: number
}

export function RiskGraph({ riskData, currentTime, duration }: RiskGraphProps) {
  const maxRisk = 100
  const height = 120
  const effectiveDuration =
    duration ?? riskData[riskData.length - 1]?.timestamp ?? 1

  const points = riskData.map((data, index) => {
    const x = (data.timestamp / effectiveDuration) * 100
    const y = height - (data.riskLevel / maxRisk) * height
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
  })

  const pathData = points.join(' ')
  const areaPathData = `${pathData} L 100 ${height} L 0 ${height} Z`

  const currentRisk = riskData.reduce((prev, curr) => {
    return Math.abs(curr.timestamp - currentTime) <
      Math.abs(prev.timestamp - currentTime)
      ? curr
      : prev
  }, riskData[0] ?? { timestamp: 0, riskLevel: 0 }).riskLevel

  const currentX = (currentTime / effectiveDuration) * 100

  return (
    <div className="risk-graph">
      <svg
        className="risk-graph__svg"
        viewBox={`0 0 100 ${height}`}
        preserveAspectRatio="none"
      >
        <line
          x1="0"
          y1={height * 0.3}
          x2="100"
          y2={height * 0.3}
          className="risk-graph__grid"
        />
        <line
          x1="0"
          y1={height * 0.7}
          x2="100"
          y2={height * 0.7}
          className="risk-graph__grid"
        />

        <defs>
          <linearGradient id="riskGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#dc2626" stopOpacity="0.55" />
            <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#16a34a" stopOpacity="0.2" />
          </linearGradient>
        </defs>

        {riskData.map((data, index) => {
          if (data.riskLevel < 70 || index === riskData.length - 1) {
            return null
          }
          const nextData = riskData[index + 1]
          const x1 = (data.timestamp / effectiveDuration) * 100
          const x2 = (nextData.timestamp / effectiveDuration) * 100
          return (
            <rect
              key={`high-risk-${index}`}
              x={x1}
              y="0"
              width={x2 - x1}
              height={height}
              className="risk-graph__highlight"
            />
          )
        })}

        <path d={areaPathData} fill="url(#riskGradient)" />
        <path d={pathData} className="risk-graph__line" />

        <line
          x1={currentX}
          y1="0"
          x2={currentX}
          y2={height}
          className="risk-graph__cursor"
        />
      </svg>

      <div className="risk-graph__label risk-graph__label--top">100%</div>
      <div className="risk-graph__label risk-graph__label--bottom">0%</div>

      <div className="risk-graph__current">
        現在:
        <span
          className={
            currentRisk >= 70
              ? 'risk-graph__current-value risk-graph__current-value--high'
              : currentRisk >= 30
              ? 'risk-graph__current-value risk-graph__current-value--medium'
              : 'risk-graph__current-value risk-graph__current-value--low'
          }
        >
          {currentRisk}%
        </span>
      </div>
    </div>
  )
}
