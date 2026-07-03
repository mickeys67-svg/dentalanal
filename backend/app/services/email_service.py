from typing import List, Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging
from jinja2 import Template

class EmailService:
    """
    이메일 발송 서비스

    SMTP를 통한 리포트 자동 발송
    - HTML 템플릿 기반
    - PDF 첨부 파일 지원
    - 일괄 발송 기능
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # SMTP 설정 (환경변수)
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("FROM_EMAIL", self.smtp_user)

    def send_report_email(
        self,
        to_emails: List[str],
        subject: str,
        report_title: str,
        client_name: str,
        summary: str,
        pdf_bytes: Optional[bytes] = None,
        pdf_filename: str = "report.pdf"
    ) -> bool:
        """
        리포트 이메일 발송

        Args:
            to_emails: 수신자 이메일 목록
            subject: 이메일 제목
            report_title: 리포트 제목
            client_name: 클라이언트 이름
            summary: 리포트 요약
            pdf_bytes: PDF 파일 바이트
            pdf_filename: PDF 파일명

        Returns:
            발송 성공 여부
        """
        try:
            # HTML 템플릿
            html_content = self._render_email_template(
                report_title=report_title,
                client_name=client_name,
                summary=summary
            )

            # MIME 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # HTML 본문
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # PDF 첨부 (옵션)
            if pdf_bytes:
                pdf_part = MIMEBase('application', 'octet-stream')
                pdf_part.set_payload(pdf_bytes)
                encoders.encode_base64(pdf_part)
                pdf_part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={pdf_filename}'
                )
                msg.attach(pdf_part)

            # SMTP 발송
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            self.logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False

    def _render_email_template(
        self,
        report_title: str,
        client_name: str,
        summary: str
    ) -> str:
        """
        이메일 HTML 템플릿 렌더링

        Args:
            report_title: 리포트 제목
            client_name: 클라이언트 이름
            summary: 리포트 요약

        Returns:
            렌더링된 HTML 문자열
        """
        template_str = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ report_title }}</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    border-bottom: 3px solid #4F46E5;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }
                .header h1 {
                    color: #4F46E5;
                    margin: 0;
                    font-size: 24px;
                }
                .content {
                    margin-bottom: 30px;
                }
                .content h2 {
                    color: #1F2937;
                    font-size: 18px;
                    margin-bottom: 10px;
                }
                .content p {
                    color: #6B7280;
                    margin: 10px 0;
                }
                .summary-box {
                    background-color: #F3F4F6;
                    border-left: 4px solid #4F46E5;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }
                .cta-button {
                    display: inline-block;
                    background-color: #4F46E5;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }
                .cta-button:hover {
                    background-color: #4338CA;
                }
                .footer {
                    text-align: center;
                    padding-top: 20px;
                    border-top: 1px solid #E5E7EB;
                    font-size: 12px;
                    color: #9CA3AF;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 KeywordLens 성과 리포트</h1>
                    <p style="margin: 10px 0 0 0; color: #6B7280;">{{ client_name }} 리포트</p>
                </div>

                <div class="content">
                    <h2>{{ report_title }}</h2>
                    <p>안녕하세요,</p>
                    <p>{{ client_name }}의 최신 마케팅 성과 분석 리포트가 완성되었습니다.</p>

                    <div class="summary-box">
                        <strong style="color: #1F2937;">📌 주요 내용</strong>
                        <p style="margin-top: 10px;">{{ summary }}</p>
                    </div>

                    <p>첨부된 PDF 파일에서 상세한 분석 결과를 확인하실 수 있습니다.</p>

                    <!-- Optional: Add CTA button
                    <a href="#" class="cta-button">대시보드에서 보기</a>
                    -->
                </div>

                <div class="footer">
                    <p>본 이메일은 KeywordLens 자동화 리포팅 시스템에서 발송되었습니다.</p>
                    <p>© 2026 KeywordLens. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        template = Template(template_str)
        return template.render(
            report_title=report_title,
            client_name=client_name,
            summary=summary
        )

    def send_test_email(self, to_email: str) -> bool:
        """
        테스트 이메일 발송

        Args:
            to_email: 수신자 이메일

        Returns:
            발송 성공 여부
        """
        return self.send_report_email(
            to_emails=[to_email],
            subject="[테스트] KeywordLens 리포트 이메일",
            report_title="테스트 리포트",
            client_name="테스트 클라이언트",
            summary="이메일 발송 테스트입니다. SMTP 설정이 정상적으로 작동하고 있습니다."
        )
