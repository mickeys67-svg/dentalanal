"use client"

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { InfoTooltip } from '@/components/common/InfoTooltip'
import { RefreshCw } from 'lucide-react'

interface PositioningTarget {
  id: string
  name: string
  type: 'OWNER' | 'COMPETITOR' | 'OTHERS'
  ranks: (number | null)[]
}

interface PositioningMapData {
  keywords: string[]
  targets: PositioningTarget[]
  snapshot_time: string | null
}

type Platform = 'NAVER_PLACE' | 'NAVER_VIEW'

interface KeywordPositioningMapProps {
  clientId: string
  platform?: Platform
  days?: number
}

const PLATFORM_LABELS: Record<Platform, string> = {
  NAVER_PLACE: '네이버 플레이스',
  NAVER_VIEW: '네이버 블로그',
}

const KeywordPositioningMap: React.FC<KeywordPositioningMapProps> = ({
  clientId,
  platform: initialPlatform = 'NAVER_PLACE',
  days = 30
}) => {
  const [activePlatform, setActivePlatform] = useState<Platform>(initialPlatform)
  const [data, setData] = useState<PositioningMapData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPositioningMap()
  }, [clientId, activePlatform, days])

  const fetchPositioningMap = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(
        `/api/v1/competitors/positioning-map/${clientId}?platform=${activePlatform}&days=${days}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('포지셔닝 맵을 불러오지 못했습니다.')
      }

      const result = await response.json()
      setData(result.data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const getRankColor = (rank: number | null): string => {
    if (rank === null) return 'bg-gray-100 text-gray-400'
    if (rank === 1) return 'bg-green-500 text-white font-bold'
    if (rank <= 3) return 'bg-green-400 text-white'
    if (rank <= 5) return 'bg-yellow-400 text-gray-900'
    if (rank <= 10) return 'bg-orange-400 text-white'
    return 'bg-red-400 text-white'
  }

  const getTypeColor = (type: string): string => {
    switch (type) {
      case 'OWNER': return 'bg-blue-500'
      case 'COMPETITOR': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const platforms: Platform[] = ['NAVER_PLACE', 'NAVER_VIEW']

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <CardTitle className="flex items-center gap-2">
            키워드 포지셔닝 맵
            <InfoTooltip
              title="키워드 포지셔닝 맵"
              content="클라이언트와 경쟁사의 키워드별 순위를 비교합니다. 숫자가 작을수록 높은 순위입니다."
            />
          </CardTitle>

          {/* 플랫폼 토글 */}
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            {platforms.map((p) => (
              <button
                key={p}
                onClick={() => setActivePlatform(p)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  activePlatform === p
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {PLATFORM_LABELS[p]}
              </button>
            ))}
          </div>
        </div>

        {data?.snapshot_time && (
          <p className="text-xs text-gray-500 mt-1">
            최종 수집: {new Date(data.snapshot_time).toLocaleString('ko-KR')}
          </p>
        )}
      </CardHeader>

      <CardContent>
        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <p className="text-sm text-red-500">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchPositioningMap}>
              <RefreshCw className="w-3 h-3 mr-1" />
              재시도
            </Button>
          </div>
        ) : !data || data.keywords.length === 0 ? (
          <p className="text-gray-500 text-center py-8 text-sm">
            {PLATFORM_LABELS[activePlatform]}에서 추적 중인 키워드가 없습니다.
          </p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border p-2 bg-gray-50 text-left sticky left-0 z-10 text-sm">
                      타겟
                    </th>
                    {data.keywords.map((keyword, idx) => (
                      <th
                        key={idx}
                        className="border p-2 bg-gray-50 text-center min-w-[80px]"
                      >
                        <div className="text-xs font-medium truncate" title={keyword}>
                          {keyword}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.targets.map((target) => (
                    <tr key={target.id} className="hover:bg-gray-50">
                      <td className="border p-2 sticky left-0 bg-white z-10">
                        <div className="flex items-center gap-2">
                          <Badge className={getTypeColor(target.type)}>
                            {target.type === 'OWNER' ? '우리' : '경쟁'}
                          </Badge>
                          <span className="font-medium text-sm">{target.name}</span>
                        </div>
                      </td>
                      {target.ranks.map((rank, idx) => (
                        <td key={idx} className="border p-1 text-center">
                          <div className={`inline-block px-2 py-1 rounded text-sm ${getRankColor(rank)}`}>
                            {rank !== null ? rank : '-'}
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 범례 */}
            <div className="mt-4 flex flex-wrap gap-3 text-xs text-gray-600">
              {[
                { color: 'bg-green-500', label: '1-3위' },
                { color: 'bg-yellow-400', label: '4-5위' },
                { color: 'bg-orange-400', label: '6-10위' },
                { color: 'bg-red-400', label: '11위 이하' },
                { color: 'bg-gray-100 border', label: '순위 없음' },
              ].map(({ color, label }) => (
                <div key={label} className="flex items-center gap-1">
                  <div className={`w-3 h-3 rounded ${color}`} />
                  <span>{label}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export default KeywordPositioningMap
