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
            import logging
            logging.error(f"Gemini API Error (Report): {str(e)}")
            return f"Gemini 리포트 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요. (Detail: {type(e).__name__})"

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
            f"- 캠페인명: {c['name']}, ROAS: {c.get('roas', 0)}%, CPC: {c.get('cpc', 0)}원, 전환수: {c.get('conversions', 0)}" 
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

    def generate_deep_diagnosis(self, benchmark_data: Dict) -> str:
        """
        AI diagnosis based on benchmark comparison results.
        """
        if not self.client:
            return "Gemini API Client not initialized."

        client_kpis = benchmark_data.get("client_kpis", {})
        industry_avg = benchmark_data.get("industry_avg", {})
        diff = benchmark_data.get("comparison", {})

        prompt = f"""
        너는 대한민국 마케팅 시장 분석 전문가이자 Gemini AI 컨설턴트야. 
        우리 병원의 광고 성과를 업종({benchmark_data.get('industry')}) 평균 데이터와 비교하여 정밀 진단 리포트를 작성해줘.

        [성과 비교 데이터]
        1. 클릭률 (CTR): 우리 병원 {client_kpis.get('ctr')}% vs 업종 평균 {industry_avg.get('avg_ctr')}% (차이: {diff.get('ctr_diff')}%)
        2. 클릭당 비용 (CPC): 우리 병원 {client_kpis.get('cpc')}원 vs 업종 평균 {industry_avg.get('avg_cpc')}원 (차이: {diff.get('cpc_diff')}원)
        3. 전환율 (CVR): 우리 병원 {client_kpis.get('cvr')}% vs 업종 평균 {industry_avg.get('avg_cvr')}% (차이: {diff.get('cvr_diff')}%)

        [요청 사항]
        - 위 수치를 바탕으로 현재 우리 병원이 업종 내에서 어느 정도 수준(상/중/하)인지 객관적으로 평가해줘.
        - 특히 차이가 크게 발생하는 지표(예: CTR이 낮거나 CPC가 높음)에 대해 원인을 분석하고, 이를 해결하기 위한 '즉시 개선 가능한 3가지 액션 플랜'을 마케팅 용어를 사용하여 제안해줘.
        - 리포트 마지막에는 이번 달의 총평과 다음 달 목표를 한 문장으로 제시해줘.

        톤앤매너: 전문적이고 신뢰감 있는 보고서 형식. 한국어로 작성.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"정밀 진단 생성 중 오류 발생: {str(e)}"
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
    def generate_efficiency_review(self, efficiency_data: Dict) -> Dict:
        """
        AI-driven review of spend vs performance efficiency.
        Returns a dict with 'overall' markdown and 'suggestions' mapping item names to strings.
        """
        if not self.client:
            return {"overall": "Gemini API Client not initialized.", "suggestions": {}}

        items = efficiency_data.get("items", [])
        overall_roas = efficiency_data.get("overall_roas", 0)
        total_spend = efficiency_data.get("total_spend", 0)
        
        items_str = "\n".join([
            f"- {i['name']}: 비용 ₩{i['spend']:,.0f}, 전환 {i['conversions']}건, ROAS {i['roas']}%, CPA ₩{i['cpa']:,.0f}"
            for i in items[:15]
        ])

        prompt = f"""
        너는 데이터 기반 퍼포먼스 마케팅 컨설턴트야. 아래의 광고 비용 대 성과 데이터를 보고 종합적인 '효율 리뷰'와 '캠페인별 개선 액션'을 작성해줘.
        
        [전체 요약]
        - 기간: {efficiency_data.get('period')}
        - 총 집행 비용: ₩{total_spend:,.0f}
        - 전체 ROAS: {overall_roas}%
        
        [세부 캠페인 성과]
        {items_str}
        
        [요청 사항]
        1. 광고 효율 총평: 단순히 수치 나열이 아닌, 현재 예산 대비 성과가 적정한지 전문가적 소견을 마크다운으로 작성해줘.
        2. 캠페인별 구체적 제안: 각 캠페인(리스트에 있는 캠페인명 정확히 사용)에 대해 1~2문장의 아주 구체적인 개선 액션(액터가 수행할 작업)을 제안해줘.
        
        [응답 형식]
        반드시 아래의 정해진 JSON 형식을 지켜서 응답해줘. JSON 외의 다른 텍스트는 포함하지 마.
        {{
            "overall": "여기에 마케팅 총평 (Markdown 형식) 작성",
            "suggestions": {{
                "캠페인명1": "구체적인 개선 제안 텍스트",
                "캠페인명2": "구체적인 개선 제안 텍스트",
                ...
            }}
        }}

        톤앤매너: 전문적이고 날카로운 비평가 스타일. 한국어로 작성.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', 
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
                contents=prompt
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            return {
                "overall": f"효율 리뷰 생성 중 오류 발생: {str(e)}",
                "suggestions": {}
            }
