import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "D-MIND | 통합 모니터링 & AI 분석 솔루션",
  description: "데이터 기반의 치과 경영 분석 및 AI 전략 제안 플랫폼, D-MIND.",
  keywords: ["치과 분석", "AI 전략", "병원 경영", "모니터링 솔루션", "D-MIND"],
  openGraph: {
    title: "D-MIND - 통합 분석 솔루션",
    description: "데이터 기반의 스마트한 병원 경영을 시작하세요.",
    type: "website",
    locale: "ko_KR",
  },
};

import Providers from "../components/providers";
import { AppLayout } from "../components/layout/AppLayout";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>
          <AppLayout>
            {children}
          </AppLayout>
        </Providers>
      </body>
    </html>
  );
}
