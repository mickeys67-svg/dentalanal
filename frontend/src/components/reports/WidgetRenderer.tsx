"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  FunnelChart,
  Funnel,
  LabelList,
} from "recharts";

interface WidgetRendererProps {
  widget: {
    id: string;
    type: string;
    title?: string;
    metrics?: string[];
  };
  data: any;
}

export function WidgetRenderer({ widget, data }: WidgetRendererProps) {
  const renderContent = () => {
    if (!data) {
      return (
        <div className="p-8 text-center text-muted-foreground">
          데이터를 불러올 수 없습니다
        </div>
      );
    }

    switch (widget.type) {
      case "KPI_GROUP":
        return renderKPIGroup();

      case "FUNNEL":
        return renderFunnel();

      case "COHORT":
        return renderCohort();

      case "ROI_COMPARISON":
        return renderROIComparison();

      case "TREND_CHART":
        return renderTrendChart();

      case "AI_DIAGNOSIS":
        return renderAIDiagnosis();

      case "BENCHMARK":
        return renderBenchmark();

      default:
        return (
          <div className="p-8 text-center text-muted-foreground">
            알 수 없는 위젯 타입: {widget.type}
          </div>
        );
    }
  };

  const renderKPIGroup = () => {
    const kpis = Array.isArray(data) ? data : [data];

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {kpis.map((kpi: any, idx: number) => (
          <Card key={idx} className="p-4">
            <p className="text-sm text-muted-foreground mb-1">{kpi.label}</p>
            <p className="text-2xl font-bold">{kpi.value?.toLocaleString()}</p>
            {kpi.change && (
              <p className={`text-xs mt-1 ${kpi.change > 0 ? "text-green-600" : "text-red-600"}`}>
                {kpi.change > 0 ? "+" : ""}{kpi.change}%
              </p>
            )}
          </Card>
        ))}
      </div>
    );
  };

  const renderFunnel = () => {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <FunnelChart>
          <Tooltip />
          <Funnel
            dataKey="value"
            data={data}
            isAnimationActive
          >
            <LabelList position="right" fill="#000" stroke="none" dataKey="name" />
          </Funnel>
        </FunnelChart>
      </ResponsiveContainer>
    );
  };

  const renderCohort = () => {
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">코호트</th>
              {data.headers?.map((h: string, idx: number) => (
                <th key={idx} className="text-center p-2">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows?.map((row: any, idx: number) => (
              <tr key={idx} className="border-b">
                <td className="p-2 font-medium">{row.cohort}</td>
                {row.values?.map((val: number, vidx: number) => (
                  <td
                    key={vidx}
                    className="text-center p-2"
                    style={{
                      backgroundColor: `rgba(79, 70, 229, ${val / 100})`,
                      color: val > 50 ? "white" : "inherit",
                    }}
                  >
                    {val}%
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderROIComparison = () => {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="roi" fill="#4F46E5" name="ROI %" />
          <Bar dataKey="spend" fill="#10B981" name="광고비" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderTrendChart = () => {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="value" stroke="#4F46E5" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderAIDiagnosis = () => {
    return (
      <div className="prose max-w-none">
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">🤖</span>
            <h3 className="text-lg font-semibold m-0">AI 진단</h3>
          </div>
          <div className="text-sm text-gray-700 whitespace-pre-wrap">
            {data.diagnosis || data.message || "AI 분석 결과가 없습니다."}
          </div>
        </div>
      </div>
    );
  };

  const renderBenchmark = () => {
    return (
      <div className="grid grid-cols-2 gap-4">
        {data.map((item: any, idx: number) => (
          <Card key={idx} className="p-4">
            <p className="text-sm text-muted-foreground mb-2">{item.metric}</p>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold">{item.your_value}</span>
              <span className="text-xs text-muted-foreground">vs</span>
              <span className="text-sm text-gray-600">{item.industry_avg}</span>
            </div>
            <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary"
                style={{
                  width: `${Math.min(
                    100,
                    (item.your_value / item.industry_avg) * 100
                  )}%`,
                }}
              />
            </div>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <Card className="p-6">
      {widget.title && (
        <h3 className="text-lg font-semibold mb-4">{widget.title}</h3>
      )}
      {renderContent()}
    </Card>
  );
}
