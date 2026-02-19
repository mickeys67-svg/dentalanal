"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ReportBuilder } from "@/components/reports/ReportBuilder";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import type { Widget } from "@/components/reports/ReportBuilder";
import { useClient } from "@/components/providers/ClientProvider";
import { toast } from "sonner";

export default function ReportBuilderPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { selectedClient } = useClient();
  const templateId = searchParams.get("template");

  const [isLoading, setIsLoading] = useState(false);
  const [initialWidgets, setInitialWidgets] = useState<Widget[]>([]);

  useEffect(() => {
    if (templateId) {
      loadTemplate(templateId);
    }
  }, [templateId]);

  const loadTemplate = async (id: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/reports/templates/${id}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const template = await response.json();
        const widgets = template.config?.widgets?.map((w: any, idx: number) => ({
          id: `widget-${idx}`,
          type: w.type,
          title: w.title || w.id,
          config: w,
        })) || [];
        setInitialWidgets(widgets);
      }
    } catch (error) {
      console.error("Failed to load template:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (widgets: Widget[]) => {
    if (!selectedClient) {
      toast.error("클라이언트를 선택해주세요");
      return;
    }

    setIsLoading(true);
    try {
      // 1. Create report template
      const templateResponse = await fetch("/api/v1/reports/templates", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          name: `사용자 정의 리포트 - ${new Date().toLocaleDateString()}`,
          description: "리포트 빌더로 생성된 커스텀 리포트",
          config: {
            layout: "grid",
            widgets: widgets.map((w) => ({
              id: w.id,
              type: w.type,
              title: w.title,
              ...w.config,
            })),
          },
        }),
      });

      if (!templateResponse.ok) {
        throw new Error("Failed to create template");
      }

      const template = await templateResponse.json();

      // 2. Create report instance
      const reportResponse = await fetch("/api/v1/reports", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          template_id: template.id,
          client_id: selectedClient.id,
          title: `커스텀 리포트 - ${new Date().toLocaleDateString()}`,
        }),
      });

      if (!reportResponse.ok) {
        throw new Error("Failed to create report");
      }

      const report = await reportResponse.json();
      toast.success("리포트가 생성되었습니다!");
      router.push(`/reports/${report.id}`);
    } catch (error) {
      console.error("Failed to save report:", error);
      toast.error("리포트 저장에 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" onClick={() => router.back()} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          뒤로 가기
        </Button>
        <h1 className="text-3xl font-bold">리포트 빌더</h1>
        <p className="text-muted-foreground mt-2">
          위젯을 드래그하여 원하는 리포트를 만들어보세요
          {selectedClient && ` — ${selectedClient.name}`}
        </p>
      </div>

      {/* Builder */}
      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">로딩 중...</p>
        </div>
      ) : (
        <ReportBuilder initialWidgets={initialWidgets} onSave={handleSave} />
      )}
    </div>
  );
}
