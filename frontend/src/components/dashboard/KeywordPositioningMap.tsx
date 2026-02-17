"use client"

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import InfoTooltip from '@/components/common/InfoTooltip'

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

interface KeywordPositioningMapProps {
  clientId: string
  platform?: 'NAVER_PLACE' | 'NAVER_VIEW' | 'NAVER_AD'
  days?: number
}

const KeywordPositioningMap: React.FC<KeywordPositioningMapProps> = ({
  clientId,
  platform = 'NAVER_PLACE',
  days = 30
}) => {
  const [data, setData] = useState<PositioningMapData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPositioningMap()
  }, [clientId, platform, days])

  const fetchPositioningMap = async () => {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/v1/competitors/positioning-map/${clientId}?platform=${platform}&days=${days}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('Failed to fetch positioning map')
      }

      const result = await response.json()
      setData(result.data)
      setError(null)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Unknown error occurred')
      }
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
      case 'OWNER':
        return 'bg-blue-500'
      case 'COMPETITOR':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            키워드 포지셔닝 맵
            <InfoTooltip text="클라이언트와 경쟁사의 키워드별 순위를 비교합니다" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>키워드 포지셔닝 맵</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-500">Error: {error}</p>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.keywords.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>키워드 포지셔닝 맵</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-center py-8">
            추적 중인 키워드가 없습니다.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          키워드 포지셔닝 맵
          <InfoTooltip text="클라이언트와 경쟁사의 키워드별 순위를 비교합니다. 숫자가 작을수록 높은 순위입니다." />
        </CardTitle>
        <div className="text-sm text-gray-500">
          {data.snapshot_time && (
            <span>최종 수집: {new Date(data.snapshot_time).toLocaleString('ko-KR')}</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="border p-2 bg-gray-50 text-left sticky left-0 z-10">
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
                      <div
                        className={`inline-block px-2 py-1 rounded text-sm ${getRankColor(rank)}`}
                      >
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
        <div className="mt-4 flex flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span>1-3위</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-yellow-400 rounded"></div>
            <span>4-5위</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-orange-400 rounded"></div>
            <span>6-10위</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-400 rounded"></div>
            <span>11위 이하</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-gray-100 border rounded"></div>
            <span>순위 없음</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default KeywordPositioningMap
