"use client";

import React from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GripVertical, Settings, Trash2 } from "lucide-react";
import type { Widget } from "./ReportBuilder";

interface SortableWidgetProps {
  widget: Widget;
  onRemove: (id: string) => void;
}

export function SortableWidget({ widget, onRemove }: SortableWidgetProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: widget.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const getWidgetIcon = (type: string) => {
    switch (type) {
      case "KPI_GROUP":
        return "📊";
      case "FUNNEL":
        return "🔽";
      case "COHORT":
        return "📈";
      case "ROI_COMPARISON":
        return "💰";
      case "TREND_CHART":
        return "📉";
      case "AI_DIAGNOSIS":
        return "🤖";
      case "BENCHMARK":
        return "🎯";
      default:
        return "📋";
    }
  };

  return (
    <Card ref={setNodeRef} style={style} className="p-4">
      <div className="flex items-center gap-4">
        {/* Drag Handle */}
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground"
        >
          <GripVertical className="w-5 h-5" />
        </button>

        {/* Widget Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getWidgetIcon(widget.type)}</span>
            <div>
              <h3 className="font-semibold">{widget.title}</h3>
              <p className="text-sm text-muted-foreground">{widget.type}</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button variant="ghost" size="sm">
            <Settings className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onRemove(widget.id)}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Widget Preview */}
      <div className="mt-4 p-4 bg-muted/50 rounded-md">
        <p className="text-sm text-muted-foreground text-center">
          위젯 미리보기 영역
        </p>
      </div>
    </Card>
  );
}
