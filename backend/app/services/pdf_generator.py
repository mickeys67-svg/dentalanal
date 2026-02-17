from typing import Dict, List, Optional
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import logging

class PDFGeneratorService:
    """
    리포트 PDF 생성 서비스

    ReportLab 기반 고품질 PDF 생성
    - 커스터마이즈 가능한 템플릿
    - 차트 및 표 포함
    - 브랜딩 (로고, 색상)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.styles = getSampleStyleSheet()

        # 커스텀 스타일 정의
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4F46E5'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=12,
            spaceBefore=12
        ))

        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceAfter=8
        ))

    def generate_report_pdf(
        self,
        report_data: Dict,
        template_config: Dict,
        client_name: str,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        리포트 PDF 생성

        Args:
            report_data: 리포트 데이터 (위젯별)
            template_config: 템플릿 설정
            client_name: 클라이언트 이름
            output_path: 출력 경로 (None이면 bytes 반환)

        Returns:
            PDF 바이트 데이터
        """
        buffer = io.BytesIO()

        # PDF 문서 생성
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Story (PDF 콘텐츠)
        story = []

        # 1. 표지
        story.extend(self._build_cover_page(client_name, template_config.get("name", "성과 리포트")))
        story.append(PageBreak())

        # 2. 위젯별 콘텐츠 생성
        widgets = template_config.get("widgets", [])

        for widget in widgets:
            widget_id = widget.get("id")
            widget_type = widget.get("type")
            widget_title = widget.get("title", widget_id)
            widget_data = report_data.get(widget_id, {})

            # 위젯 제목
            story.append(Paragraph(widget_title, self.styles['CustomHeading']))
            story.append(Spacer(1, 12))

            # 위젯 타입별 렌더링
            if widget_type == "KPI_GROUP":
                story.extend(self._render_kpi_group(widget_data))
            elif widget_type == "FUNNEL":
                story.extend(self._render_funnel(widget_data))
            elif widget_type == "COHORT":
                story.extend(self._render_cohort(widget_data))
            elif widget_type == "ROI_COMPARISON":
                story.extend(self._render_roi_comparison(widget_data))
            elif widget_type == "TREND_CHART":
                story.extend(self._render_trend_chart(widget_data))
            elif widget_type == "AI_DIAGNOSIS":
                story.extend(self._render_ai_diagnosis(widget_data))
            elif widget_type == "BENCHMARK":
                story.extend(self._render_benchmark(widget_data))

            story.append(Spacer(1, 20))

        # 3. PDF 생성
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # 파일로 저장 (옵션)
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def _build_cover_page(self, client_name: str, report_title: str) -> List:
        """표지 페이지 생성"""
        elements = []

        # 타이틀
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(report_title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))

        # 클라이언트 이름
        elements.append(Paragraph(
            f"<b>{client_name}</b>",
            self.styles['CustomHeading']
        ))

        # 생성일
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            f"생성일: {datetime.now().strftime('%Y년 %m월 %d일')}",
            self.styles['CustomBody']
        ))

        # 로고 (옵션)
        # elements.append(Spacer(1, inch))
        # elements.append(RLImage('path/to/logo.png', width=2*inch, height=1*inch))

        return elements

    def _render_kpi_group(self, data: Dict) -> List:
        """KPI 그룹 렌더링"""
        elements = []

        kpis = data.get("kpis", [])
        if not kpis:
            return elements

        # 테이블 데이터 생성
        table_data = []
        for kpi in kpis:
            table_data.append([
                Paragraph(f"<b>{kpi.get('label', 'N/A')}</b>", self.styles['CustomBody']),
                Paragraph(f"{kpi.get('value', 0):,}", self.styles['CustomBody']),
                Paragraph(
                    f"<font color='{'green' if kpi.get('change', 0) > 0 else 'red'}'>{kpi.get('change', 0):+.1f}%</font>",
                    self.styles['CustomBody']
                )
            ])

        table = Table(table_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB'))
        ]))

        elements.append(table)
        return elements

    def _render_funnel(self, data: Dict) -> List:
        """퍼널 차트 렌더링 (이미지로)"""
        elements = []

        stages = data.get("stages", [])
        if not stages:
            return elements

        # Matplotlib로 차트 생성
        fig, ax = plt.subplots(figsize=(6, 4))

        labels = [s.get("name", "") for s in stages]
        values = [s.get("value", 0) for s in stages]

        ax.barh(labels, values, color='#4F46E5')
        ax.set_xlabel('사용자 수')
        ax.set_title('전환 퍼널')

        # 이미지로 변환
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()

        img = RLImage(img_buffer, width=5*inch, height=3*inch)
        elements.append(img)

        return elements

    def _render_cohort(self, data: Dict) -> List:
        """코호트 테이블 렌더링"""
        elements = []

        headers = data.get("headers", [])
        rows = data.get("rows", [])

        if not headers or not rows:
            return elements

        # 테이블 데이터
        table_data = [["코호트"] + headers]

        for row in rows:
            table_data.append([row.get("cohort", "")] + [f"{v}%" for v in row.get("values", [])])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        return elements

    def _render_roi_comparison(self, data: Dict) -> List:
        """ROI 비교 차트 렌더링"""
        elements = []

        campaigns = data.get("campaigns", [])
        if not campaigns:
            return elements

        # Matplotlib로 막대 차트 생성
        fig, ax = plt.subplots(figsize=(6, 4))

        names = [c.get("name", "")[:15] for c in campaigns]  # 이름 짧게
        roi_values = [c.get("roi", 0) for c in campaigns]

        ax.bar(names, roi_values, color='#10B981')
        ax.set_ylabel('ROI (%)')
        ax.set_title('캠페인별 ROI 비교')
        ax.tick_params(axis='x', rotation=45)

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()

        img = RLImage(img_buffer, width=5*inch, height=3*inch)
        elements.append(img)

        return elements

    def _render_trend_chart(self, data: Dict) -> List:
        """트렌드 라인 차트 렌더링"""
        elements = []

        trend_data = data.get("data", [])
        if not trend_data:
            return elements

        # Matplotlib로 라인 차트 생성
        fig, ax = plt.subplots(figsize=(6, 4))

        dates = [d.get("date", "") for d in trend_data]
        values = [d.get("value", 0) for d in trend_data]

        ax.plot(dates, values, marker='o', color='#4F46E5', linewidth=2)
        ax.set_xlabel('날짜')
        ax.set_ylabel('지표')
        ax.set_title('추이 분석')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()

        img = RLImage(img_buffer, width=5*inch, height=3*inch)
        elements.append(img)

        return elements

    def _render_ai_diagnosis(self, data: Dict) -> List:
        """AI 진단 결과 렌더링"""
        elements = []

        diagnosis = data.get("diagnosis", "AI 분석 결과가 없습니다.")

        # 박스로 강조
        box_style = ParagraphStyle(
            'AIBox',
            parent=self.styles['CustomBody'],
            backColor=colors.HexColor('#F3F4F6'),
            borderPadding=10,
            borderWidth=1,
            borderColor=colors.HexColor('#D1D5DB'),
            leftIndent=10,
            rightIndent=10
        )

        elements.append(Paragraph(f"<b>🤖 Gemini AI 진단</b>", self.styles['CustomHeading']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(diagnosis, box_style))

        return elements

    def _render_benchmark(self, data: Dict) -> List:
        """벤치마크 비교 렌더링"""
        elements = []

        benchmarks = data.get("benchmarks", [])
        if not benchmarks:
            return elements

        table_data = [["지표", "내 값", "업종 평균", "차이"]]

        for bm in benchmarks:
            diff = bm.get("your_value", 0) - bm.get("industry_avg", 0)
            table_data.append([
                bm.get("metric", ""),
                f"{bm.get('your_value', 0):.1f}",
                f"{bm.get('industry_avg', 0):.1f}",
                f"<font color='{'green' if diff > 0 else 'red'}'>{diff:+.1f}</font>"
            ])

        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        return elements

    def _add_page_number(self, canvas_obj, doc):
        """페이지 번호 추가"""
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 9)
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.drawRightString(A4[0] - 72, 30, text)
        canvas_obj.restoreState()
