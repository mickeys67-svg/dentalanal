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
  title: "KeywordLens | 키워드·SNS 통합 분석 어드민",
  description: "네이버 검색량과 4대 SNS 언급량을 다중 키워드로 조회·분석하는 통합 어드민, KeywordLens.",
  keywords: ["키워드 분석", "검색량 분석", "SNS 언급량", "마케팅 데이터", "KeywordLens"],
  openGraph: {
    title: "KeywordLens - 키워드·SNS 통합 분석 어드민",
    description: "데이터로 읽는 마케팅 인사이트를 시작하세요.",
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
    <html lang="ko">
      <head>
        {/* KeywordLens 디자인 폰트: Pretendard(본문) + Noto Serif KR(숫자·헤드라인) */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css"
        />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;600;700&display=swap"
        />
      </head>
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
