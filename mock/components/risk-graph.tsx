"use client"

interface RiskGraphProps {
  riskData: Array<{ timestamp: number; riskLevel: number }>
  currentTime: number
}

export function RiskGraph({ riskData, currentTime }: RiskGraphProps) {
  const maxRisk = 100
  const width = 100 // パーセント
  const height = 120 // ピクセル

  // SVGパスを生成
  const points = riskData.map((data, index) => {
    const x = (data.timestamp / riskData[riskData.length - 1].timestamp) * 100
    const y = height - (data.riskLevel / maxRisk) * height
    return `${index === 0 ? "M" : "L"} ${x} ${y}`
  })

  const pathData = points.join(" ")

  // エリアの塗りつぶし用パス
  const areaPathData = `${pathData} L 100 ${height} L 0 ${height} Z`

  const getCurrentRisk = () => {
    const closest = riskData.reduce((prev, curr) => {
      return Math.abs(curr.timestamp - currentTime) < Math.abs(prev.timestamp - currentTime) ? curr : prev
    })
    return closest.riskLevel
  }

  const currentRisk = getCurrentRisk()

  return (
    <div className="relative h-32 w-full">
      <svg className="h-full w-full" viewBox={`0 0 100 ${height}`} preserveAspectRatio="none">
        {/* グリッドライン */}
        <line
          x1="0"
          y1={height * 0.3}
          x2="100"
          y2={height * 0.3}
          stroke="currentColor"
          strokeWidth="0.2"
          className="text-border"
          strokeDasharray="2,2"
        />
        <line
          x1="0"
          y1={height * 0.7}
          x2="100"
          y2={height * 0.7}
          stroke="currentColor"
          strokeWidth="0.2"
          className="text-border"
          strokeDasharray="2,2"
        />

        {/* エリアグラデーション */}
        <defs>
          <linearGradient id="riskGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="hsl(var(--destructive))" stopOpacity="0.6" />
            <stop offset="50%" stopColor="hsl(var(--warning))" stopOpacity="0.4" />
            <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity="0.2" />
          </linearGradient>
        </defs>

        {riskData.map((data, index) => {
          if (data.riskLevel >= 70 && index < riskData.length - 1) {
            const nextData = riskData[index + 1]
            const x1 = (data.timestamp / riskData[riskData.length - 1].timestamp) * 100
            const x2 = (nextData.timestamp / riskData[riskData.length - 1].timestamp) * 100
            return (
              <rect
                key={`high-risk-${index}`}
                x={x1}
                y="0"
                width={x2 - x1}
                height={height}
                fill="hsl(var(--destructive))"
                opacity="0.1"
              />
            )
          }
          return null
        })}

        {/* リスクエリア */}
        <path d={areaPathData} fill="url(#riskGradient)" />

        {/* リスクライン */}
        <path d={pathData} fill="none" stroke="hsl(var(--primary))" strokeWidth="0.5" className="drop-shadow-lg" />

        {/* 現在時刻のインジケーター */}
        <line
          x1={(currentTime / 90) * 100}
          y1="0"
          x2={(currentTime / 90) * 100}
          y2={height}
          stroke="hsl(var(--primary))"
          strokeWidth="0.3"
          opacity="0.8"
        />
      </svg>

      {/* リスクレベルラベル */}
      <div className="absolute left-0 top-0 text-xs text-muted-foreground">100%</div>
      <div className="absolute bottom-0 left-0 text-xs text-muted-foreground">0%</div>

      <div className="absolute right-2 top-2 rounded bg-background/90 px-2 py-1 text-xs font-semibold backdrop-blur-sm">
        現在:{" "}
        <span className={currentRisk >= 70 ? "text-destructive" : currentRisk >= 30 ? "text-warning" : "text-success"}>
          {currentRisk}%
        </span>
      </div>
    </div>
  )
}
