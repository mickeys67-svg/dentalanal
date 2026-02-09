export function Header() {
    return (
        <header className="bg-white shadow">
            <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 flex justify-between items-center">
                <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                    Dashboard
                </h1>
                <div className="flex items-center gap-4">
                    {/* User Profile or Notifications could go here */}
                    <span className="text-sm text-gray-500">Admin User</span>
                </div>
            </div>
        </header>
    );
}
