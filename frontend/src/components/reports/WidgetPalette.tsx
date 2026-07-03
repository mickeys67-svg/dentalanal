"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface WidgetPaletteProps {
  onSelect: (type: string, title: string) => void;
  onClose: () => void;
}

const WIDGET_TYPES = [
  {
    type: "KPI_GROUP",
    title: "KPI 지표 그룹",
    description: "주요 성과 지표를 한눈에 표시",
    icon: "📊",
  },
  {
    type: "FUNNEL",
    title: "전환 퍼널 분석",
    description: "단계별 전환율 시각화",
    icon: "🔽",
  },
  {
    type: "COHORT",
    title: "코호트 분석",
    description: "사용자 그룹별 리텐션 추적",
    icon: "📈",
  },
  {
    type: "ROI_COMPARISON",
    title: "ROI 비교",
    description: "캠페인별 투자 수익률 비교",
    icon: "💰",
  },
  {
    type: "TREND_CHART",
    title: "트렌드 차트",
    description: "시계열 데이터 추이 분석",
    icon: "📉",
  },
  {
    type: "AI_DIAGNOSIS",
    title: "AI 진단 리포트",
    description: "AI 기반 성과 분석",
    icon: "🤖",
  },
  {
    type: "BENCHMARK",
    title: "업종 벤치마크",
    description: "업종 평균과 비교",
    icon: "🎯",
  },
];

export function WidgetPalette({ onSelect, onClose }: WidgetPaletteProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="max-w-4xl w-full mx-4 p-6 max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">위젯 선택</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Widget Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {WIDGET_TYPES.map((widget) => (
            <Card
              key={widget.type}
              className="p-4 cursor-pointer hover:border-primary transition-colors"
              onClick={() => onSelect(widget.type, widget.title)}
            >
              <div className="flex items-start gap-3">
                <span className="text-3xl">{widget.icon}</span>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">{widget.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {widget.description}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
}
