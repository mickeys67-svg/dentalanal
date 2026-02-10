import os
from google import genai
from google.genai import types
from typing import List, Dict

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_marketing_report(self, keyword: str, sov_data: float, competitors: List[Dict]) -> str:
        platform_name = "네이버 플레이스" if "place" in keyword.lower() or sov_data > 0 else "네이버 뷰"
        
        comp_str = "\n".join([f"- {c['name']}: 점유율 {c['share']:.1f}%, 평균 순위 {c['avg_rank']:.1f}위" for c in competitors[:5]])
        
        prompt = f"""
치과 마케팅 분석 리포트를 작성해줘. 너는 구글의 Gemini AI 마케팅 전문 컨설턴트야.

[분석 환경]
- 분석 키워드: {keyword}
- 플랫폼: {platform_name}
- 우리 병원( {os.getenv('TARGET_HOSPITAL_NAME', '우리 병원')} )의 점유율(SOV): {sov_data:.1f}%

[상위 경쟁사 현황]
{comp_str}

위 데이터를 바탕으로 다음 내용을 포함한 마케팅 리포트를 전문적이고 분석적으로 작성해줘 (한국어):
1. 시장 지배력 분석: 현재 키워드 시장에서의 우리 병원의 위치와 경쟁 강도
2. 경쟁사 전략 추론: 상위 노출되는 병원들의 공용 강점(리뷰 수, 정보 충실도 등) 분석
3. 전략적 개선안: 점유율 확대를 위한 구체적인 실행 방안 (예: 블로그 콘텐츠 최적화, 플레이스 예약 연동 등)
4. 성과 예측: 제언을 실행했을 시 예상되는 노출 및 유입 증대 효과

응답은 마케팅 보고서 형식으로 본문 줄바꿈을 적절히 사용하여 읽기 쉽게 작성해줘.
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Gemini 리포트 생성 중 오류가 발생했습니다: {str(e)}"

    def generate_ad_copy(self, swot_data: Dict, target_audience: str, key_proposition: str) -> List[Dict]:
        """
        Generate multiple ad copy options based on SWOT and target audience.
        """
        if not self.client:
            return [{"title": "API Key Missing", "body": "GOOGLE_API_KEY가 설정되지 않았습니다."}]

        prompt = f"""
        너는 전문 퍼포먼스 마케팅 카피라이터야. 아래 정보를 바탕으로 클릭율(CTR)을 극대화할 수 있는 광고 카피 3가지를 작성해줘.
        
        [병원 SWOT 분석]
        - 강점: {', '.join(swot_data.get('strengths', []))}
        - 약점: {', '.join(swot_data.get('weaknesses', []))}
        - 기회: {', '.join(swot_data.get('opportunities', []))}
        - 위협: {', '.join(swot_data.get('threats', []))}
        
        [타겟 오디언스]: {target_audience}
        [핵심 소구점]: {key_proposition}
        
        각 카피는 다음 형식을 지켜줘:
        1. 제목 (헤드라인, 25자 이내)
        2. 설명 (본문, 70자 이내)
        3. 소구 전략 (왜 이 카피가 효과적인지 짧은 설명)
        
        응답은 반드시 한국어로 작성하고, JSON 형식이 아닌 읽기 시각적으로 구분된 텍스트로 작성해줘.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            # Simple simulation of parsing text into items for simplicity in this bridge
            return [{"content": response.text}]
        except Exception as e:
            return [{"content": f"카피 생성 실패: {str(e)}"}]

    def analyze_performance_optimization(self, campaigns: List[Dict]) -> List[Dict]:
        """
        Analyze campaign performance and provide optimization recommendations.
        """
        if not self.client:
            return []

        campaign_data = "\n".join([
            f"- 캠페인명: {c['name']}, ROAS: {c['roas']}%, CPC: {c['cpc']}원, 전환수: {c['conversions']}" 
            for c in campaigns
        ])

        prompt = f"""
        너는 데이터 기반 퍼포먼스 마케팅 분석가야. 아래의 광고 성과 데이터를 보고 개선이 시급한 항목과 구체적인 최적화 방안을 제안해줘.
        
        [현재 캠페인 데이터]
        {campaign_data}
        
        [분석 요청 사항]
        1. 현재 전체적인 성과 요약 (ROAS 기준)
        2. '주의'가 필요한 캠페인 식별 및 사유
        3. 구체적인 액션 플랜 (예: 입찰가 하향, 소재 교체, 제외 키워드 추가 등)
        
        전문적인 마케팅 톤으로 답변해줘.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            return [{"recommendation": response.text}]
        except Exception as e:
            return [{"recommendation": f"분석 실패: {str(e)}"}]
    def generate_swot_analysis(self, hospital_name: str, competitor_info: List[Dict]) -> str:
        """
        AI generated SWOT based on competitor presence.
        """
        if not self.client:
             return "API Key Missing"

        comp_data = "\n".join([f"- {c['name']}: {c['share']:.1f}% 점유" for c in competitor_info[:3]])
        
        prompt = f"""
        우리 병원({hospital_name})을 위한 마케팅 SWOT 분석을 해줘.
        
        [주요 경쟁사 점유율]
        {comp_data}
        
        주변 경쟁 상황을 고려하여 우리 병원의 강점(Strengths), 약점(Weaknesses), 기회(Opportunities), 위협(Threats) 요인을 전문적인 마케팅 시각에서 분석해줘.
        각 항목별로 2~3가지의 구체적인 포인트를 짚어줘.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"SWOT 분석 실패: {str(e)}"
