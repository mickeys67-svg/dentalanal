import os
import google.generativeai as genai
from typing import List, Dict

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY") # Gemini uses GOOGLE_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    def generate_marketing_report(self, keyword: str, sov_data: float, competitors: List[Dict]) -> str:
        if not self.model:
            return "Gemini AI 분석을 위한 API 키가 설정되지 않았습니다. (.env 파일에 GOOGLE_API_KEY를 추가해주세요)"

        comp_str = "\n".join([f"- {c['name']}: 점유율 {c['share']:.1f}%, 평균 순위 {c['avg_rank']:.1f}위" for c in competitors[:5]])
        
        prompt = f"""
치과 마케팅 분석 리포트를 작성해줘. 너는 구글의 Gemini AI 마케팅 분석가야.

분석 키워드: {keyword}
나의 병원 SOV (점유율): {sov_data:.1f}%

상위 경쟁사 현황:
{comp_str}

위 데이터를 바탕으로 다음 내용을 포함한 마케팅 제언을 전문적이고 분석적으로 작성해줘 (한국어로):
1. 현재 시장 경쟁 상황 요약
2. 주요 경쟁 병원의 분석 (강점 및 노출 전략 추측)
3. 우리 병원의 마케팅 개선 방향 (순위 상승 및 점유율 확대 전략)
4. 향후 실행 방안 제언 (구체적인 액션 아이템)

응답은 마크다운 형식을 사용하지 말고, 읽기 편한 텍스트 줄바꿈 형식으로 작성해줘.
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Gemini 리포트 생성 중 오류가 발생했습니다: {str(e)}"
