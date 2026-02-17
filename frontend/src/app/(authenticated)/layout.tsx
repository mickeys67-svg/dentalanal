import { AppSidebar } from "@/components/layout/AppSidebar";
import { AppHeader } from "@/components/layout/AppHeader";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppSidebar />
            <div className="md:ml-64 flex flex-col min-h-screen">
                <AppHeader />
                <main className="flex-1 p-6 space-y-6 overflow-y-auto">
                    {children}
                </main>
            </div>
        </div>
    );
}
