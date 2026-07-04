'use client';

interface RankItem {
    rank: number;
    title: string;
    blog_name?: string;
    keyword: string;
    link?: string;
    created_at?: string;
}

interface RankTableProps {
    data: RankItem[];
    title: string;
    targetHospital?: string;
    platform?: 'NAVER_PLACE' | 'NAVER_VIEW';
}

export function RankTable({ data, title, targetHospital }: RankTableProps) {
    return (
        <div className="bg-card p-6 rounded-lg shadow overflow-hidden">
            <h3 className="text-lg font-medium leading-6 text-foreground mb-4">{title}</h3>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-background">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Rank
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Title
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Source
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Link
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-card divide-y divide-border">
                        {data.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-4 text-center text-sm text-muted-foreground">
                                    No data available
                                </td>
                            </tr>
                        ) : (
                            data.map((item, idx) => {
                                const isTarget = targetHospital && (item.title.includes(targetHospital) || item.blog_name?.includes(targetHospital));
                                return (
                                    <tr key={idx} className={isTarget ? "bg-blue-50" : ""}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                                            {item.rank}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground truncate max-w-xs" title={item.title}>
                                            <span className={isTarget ? "font-bold text-blue-700" : ""}>{item.title}</span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                            {item.blog_name || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-500 hover:text-blue-700">
                                            {item.link ? (
                                                <a href={item.link} target="_blank" rel="noopener noreferrer">
                                                    View
                                                </a>
                                            ) : (
                                                '-'
                                            )}
                                        </td>
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
