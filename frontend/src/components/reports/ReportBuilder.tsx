"use client";

import React, { useState } from "react";
import { DndContext, DragEndEvent, closestCenter } from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { WidgetPalette } from "./WidgetPalette";
import { SortableWidget } from "./SortableWidget";
import { Plus, Save, Eye } from "lucide-react";

export interface Widget {
  id: string;
  type: string;
  title: string;
  config?: Record<string, any>;
}

interface ReportBuilderProps {
  initialWidgets?: Widget[];
  onSave?: (widgets: Widget[]) => void;
}

export function ReportBuilder({ initialWidgets = [], onSave }: ReportBuilderProps) {
  const [widgets, setWidgets] = useState<Widget[]>(initialWidgets);
  const [reportTitle, setReportTitle] = useState("새 리포트");
  const [showPalette, setShowPalette] = useState(false);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setWidgets((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleAddWidget = (type: string, title: string) => {
    const newWidget: Widget = {
      id: `widget-${Date.now()}`,
      type,
      title,
      config: {},
    };
    setWidgets([...widgets, newWidget]);
    setShowPalette(false);
  };

  const handleRemoveWidget = (id: string) => {
    setWidgets(widgets.filter((w) => w.id !== id));
  };

  const handleSave = () => {
    if (onSave) {
      onSave(widgets);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Input
          value={reportTitle}
          onChange={(e) => setReportTitle(e.target.value)}
          className="max-w-md text-2xl font-bold"
        />
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Eye className="w-4 h-4 mr-2" />
            미리보기
          </Button>
          <Button onClick={handleSave} size="sm">
            <Save className="w-4 h-4 mr-2" />
            저장
          </Button>
        </div>
      </div>

      {/* Widget Canvas */}
      <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={widgets.map((w) => w.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-4">
            {widgets.length === 0 ? (
              <Card className="p-12 text-center border-dashed">
                <p className="text-muted-foreground mb-4">위젯을 추가하여 리포트를 구성하세요</p>
                <Button onClick={() => setShowPalette(true)} variant="outline">
                  <Plus className="w-4 h-4 mr-2" />
                  위젯 추가
                </Button>
              </Card>
            ) : (
              widgets.map((widget) => (
                <SortableWidget
                  key={widget.id}
                  widget={widget}
                  onRemove={handleRemoveWidget}
                />
              ))
            )}
          </div>
        </SortableContext>
      </DndContext>

      {/* Add Widget Button */}
      {widgets.length > 0 && (
        <Button onClick={() => setShowPalette(true)} variant="outline" className="w-full">
          <Plus className="w-4 h-4 mr-2" />
          위젯 추가
        </Button>
      )}

      {/* Widget Palette Modal */}
      {showPalette && (
        <WidgetPalette
          onSelect={handleAddWidget}
          onClose={() => setShowPalette(false)}
        />
      )}
    </div>
  );
}
