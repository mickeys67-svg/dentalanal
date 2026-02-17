"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ExternalLink, MessageSquare, Loader2 } from "lucide-react";
import { KeywordRank } from "@/types";
import { UI_TEXT } from "@/lib/i18n";
import { format } from "date-fns";

interface MentionFeedProps {
    data: KeywordRank[];
    isLoading: boolean;
}

export function MentionFeed({ data, isLoading }: MentionFeedProps) {
    if (isLoading) {
        return (
            <Card className="h-[400px] flex items-center justify-center">
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <p>{UI_TEXT.VIRAL.LOADING}</p>
                </div>
            </Card>
        );
    }

    if (!data || data.length === 0) {
        return (
            <Card className="h-[400px] flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                    <MessageSquare className="h-10 w-10 mx-auto mb-2 opacity-20" />
                    <p>{UI_TEXT.VIRAL.EMPTY_DESC}</p>
                </div>
            </Card>
        );
    }

    return (
        <Card className="h-[400px] flex flex-col">
            <CardHeader className="pb-3">
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-blue-500" />
                    {UI_TEXT.VIRAL.FEED_TITLE}
                    <Badge variant="secondary" className="ml-auto">
                        {data.length} Posts
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-hidden">
                <ScrollArea className="h-full px-6 pb-4">
                    <div className="space-y-4 pt-1">
                        {data.map((item, index) => (
                            <div key={index} className="flex flex-col gap-2 p-3 rounded-lg border bg-slate-50/50 hover:bg-slate-100/50 transition-colors">
                                <div className="flex items-start justify-between gap-2">
                                    <h4 className="font-medium text-sm text-gray-900 leading-snug line-clamp-2">
                                        {item.title.replace(/<[^>]*>?/gm, '')} {/* Remove HTML tags if any */}
                                    </h4>
                                    <Badge variant="outline" className={`shrink-0 text-[10px] ${item.blog_name?.includes('cafe') ? 'bg-orange-50 text-orange-600 border-orange-200' : 'bg-green-50 text-green-600 border-green-200'}`}>
                                        {item.blog_name || UI_TEXT.VIRAL.SOURCE_BLOG}
                                    </Badge>
                                </div>

                                <div className="flex items-center justify-between text-xs text-muted-foreground mt-1">
                                    <span>
                                        {item.created_at ? format(new Date(item.created_at), UI_TEXT.VIRAL.DATE_FORMAT) : format(new Date(), UI_TEXT.VIRAL.DATE_FORMAT)}
                                    </span>
                                    {item.link && (
                                        <a
                                            href={item.link}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="flex items-center gap-1 hover:text-blue-600 transition-colors"
                                        >
                                            {UI_TEXT.VIRAL.VIEW_ORIGINAL}
                                            <ExternalLink className="w-3 h-3" />
                                        </a>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
