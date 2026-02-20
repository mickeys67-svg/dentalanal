/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    eslint: {
        ignoreDuringBuilds: true,
    },
    typescript: {
        ignoreBuildErrors: false,
    },
    // API 프록시: /api/** 요청을 백엔드로 라우팅
    async rewrites() {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        return {
            beforeFiles: [
                {
                    source: '/api/:path*',
                    destination: `${backendUrl}/api/:path*`,
                },
                {
                    source: '/health',
                    destination: `${backendUrl}/health`,
                },
            ],
        };
    },
};

module.exports = nextConfig;
