"""
🔍 데이터 디버깅 진단 시스템

현재 상황:
- SetupWizard에서 "조사시작" 버튼 클릭
- Naver 데이터 수집 중
- 하지만 데이터가 제대로 저장되거나 표시되지 않음

진단 목표:
1. 데이터베이스 상태 확인
2. 스크래핑 파이프라인 추적
3. API 응답 검증
4. 데이터 정규화 확인
5. 병목 지점 식별
"""

import asyncio
import logging
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataDiagnostic:
    """데이터 디버깅 진단 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "sections": {}
        }
    
    async def run_full_diagnosis(self):
        """전체 진단 실행"""
        
        logger.info("=" * 80)
        logger.info("🔍 데이터 디버깅 진단 시작")
        logger.info("=" * 80)
        
        # Step 1: 데이터베이스 테이블 상태
        await self._diagnose_database_tables()
        
        # Step 2: Client 데이터 확인
        await self._diagnose_clients()
        
        # Step 3: Keywords 데이터
        await self._diagnose_keywords()
        
        # Step 4: Targets 데이터
        await self._diagnose_targets()
        
        # Step 5: DailyRanks (중요!)
        await self._diagnose_daily_ranks()
        
        # Step 6: 스크래핑 로그
        await self._diagnose_scraping_logs()
        
        # Step 7: API 응답 캐시
        await self._diagnose_analytics_cache()
        
        # Step 8: AnalysisHistory (사용자 쿼리)
        await self._diagnose_analysis_history()
        
        # Step 9: 데이터 흐름 추적
        await self._trace_data_flow()
        
        return self.report
    
    async def _diagnose_database_tables(self):
        """Step 1: 데이터베이스 테이블 상태"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 1️⃣ : 데이터베이스 테이블 상태")
        logger.info("="*80)
        
        try:
            # SQLAlchemy inspector 사용
            inspector = inspect(self.db.bind)
            tables = inspector.get_table_names()
            
            logger.info(f"\n✅ 총 테이블 수: {len(tables)}")
            logger.info("\n필수 테이블 확인:")
            
            required_tables = [
                'clients', 'keywords', 'targets', 'daily_ranks',
                'platform_connections', 'analysis_history', 'raw_scraping_logs'
            ]
            
            table_status = {}
            for table in required_tables:
                exists = table in tables
                status = "✅" if exists else "❌"
                logger.info(f"  {status} {table}")
                table_status[table] = exists
                
                if exists:
                    # 각 테이블의 행 개수
                    try:
                        count = self.db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                        logger.info(f"     └─ 행 개수: {count}")
                    except Exception as e:
                        logger.warning(f"     └─ 행 개수 확인 실패: {e}")
            
            self.report["sections"]["tables"] = table_status
            
        except Exception as e:
            logger.error(f"❌ 테이블 진단 실패: {e}")
            self.report["sections"]["tables"] = {"error": str(e)}
    
    async def _diagnose_clients(self):
        """Step 2: Client 데이터 확인"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 2️⃣ : Client 데이터")
        logger.info("="*80)
        
        try:
            from app.models.models import Client
            
            clients = self.db.query(Client).all()
            
            logger.info(f"\n✅ 총 Client 수: {len(clients)}")
            
            if clients:
                for client in clients[:5]:  # 처음 5개만
                    logger.info(f"\n📌 Client: {client.name} ({client.id})")
                    logger.info(f"   ├─ Agency: {client.agency_id}")
                    logger.info(f"   ├─ Industry: {client.industry}")
                    logger.info(f"   ├─ Created: {client.created_at}")
                    logger.info(f"   └─ Keywords: {len(client.keywords)}")
                    
                    # 각 client의 keywords
                    if client.keywords:
                        logger.info(f"      Keywords: {[k.term for k in client.keywords[:3]]}")
                    
                    # 각 client의 DailyRanks
                    daily_rank_count = len(client.daily_ranks)
                    logger.info(f"      DailyRanks: {daily_rank_count}")
            else:
                logger.warning("⚠️  Client가 없습니다!")
            
            self.report["sections"]["clients"] = {
                "count": len(clients),
                "details": [
                    {
                        "name": c.name,
                        "id": str(c.id),
                        "keywords": len(c.keywords),
                        "daily_ranks": len(c.daily_ranks)
                    }
                    for c in clients[:3]
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Client 진단 실패: {e}")
            self.report["sections"]["clients"] = {"error": str(e)}
    
    async def _diagnose_keywords(self):
        """Step 3: Keywords 데이터"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 3️⃣ : Keywords 데이터")
        logger.info("="*80)
        
        try:
            from app.models.models import Keyword
            
            keywords = self.db.query(Keyword).all()
            
            logger.info(f"\n✅ 총 Keyword 수: {len(keywords)}")
            
            if keywords:
                logger.info("\n최근 Keywords:")
                for kw in keywords[-5:]:
                    logger.info(f"  📝 {kw.term}")
                    logger.info(f"     ├─ Client ID: {kw.client_id}")
                    logger.info(f"     ├─ Category: {kw.category}")
                    logger.info(f"     └─ DailyRanks: {len(kw.daily_ranks)}")
            else:
                logger.warning("⚠️  Keywords가 없습니다!")
            
            self.report["sections"]["keywords"] = {
                "count": len(keywords)
            }
        
        except Exception as e:
            logger.error(f"❌ Keywords 진단 실패: {e}")
            self.report["sections"]["keywords"] = {"error": str(e)}
    
    async def _diagnose_targets(self):
        """Step 4: Targets 데이터"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 4️⃣ : Targets 데이터")
        logger.info("="*80)
        
        try:
            from app.models.models import Target
            
            targets = self.db.query(Target).all()
            
            logger.info(f"\n✅ 총 Target 수: {len(targets)}")
            
            if targets:
                logger.info("\nTargets (타입별):")
                types = {}
                for target in targets:
                    t = str(target.type)
                    if t not in types:
                        types[t] = 0
                    types[t] += 1
                
                for t_type, count in types.items():
                    logger.info(f"  {t_type}: {count}")
            else:
                logger.warning("⚠️  Targets가 없습니다!")
            
            self.report["sections"]["targets"] = {
                "count": len(targets)
            }
        
        except Exception as e:
            logger.error(f"❌ Targets 진단 실패: {e}")
            self.report["sections"]["targets"] = {"error": str(e)}
    
    async def _diagnose_daily_ranks(self):
        """Step 5: DailyRanks (매우 중요!)"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 5️⃣ : DailyRanks 데이터 (🔴 핵심!)")
        logger.info("="*80)
        
        try:
            from app.models.models import DailyRank
            
            daily_ranks = self.db.query(DailyRank).all()
            logger.info(f"\n✅ 총 DailyRank 수: {len(daily_ranks)}")
            
            if not daily_ranks:
                logger.error("🔴 DailyRanks가 비어있습니다! (데이터 수집이 실패했을 가능성)")
            
            # 최근 DailyRanks
            if daily_ranks:
                recent = sorted(daily_ranks, key=lambda x: x.captured_at, reverse=True)[:5]
                logger.info("\n최근 DailyRanks (5개):")
                
                for dr in recent:
                    logger.info(f"\n  🔍 Rank: {dr.rank} ({dr.platform})")
                    logger.info(f"     ├─ Keyword: {dr.keyword.term if dr.keyword else 'N/A'}")
                    logger.info(f"     ├─ Target: {dr.target.name if dr.target else 'N/A'}")
                    logger.info(f"     ├─ Client: {dr.client_id}")
                    logger.info(f"     ├─ Rank Change: {dr.rank_change}")
                    logger.info(f"     └─ Captured: {dr.captured_at}")
            
            # 플랫폼별 분포
            platform_dist = {}
            for dr in daily_ranks:
                p = str(dr.platform)
                if p not in platform_dist:
                    platform_dist[p] = 0
                platform_dist[p] += 1
            
            logger.info(f"\nDailyRanks 분포 (플랫폼별):")
            for platform, count in platform_dist.items():
                logger.info(f"  {platform}: {count}")
            
            self.report["sections"]["daily_ranks"] = {
                "count": len(daily_ranks),
                "platforms": platform_dist
            }
        
        except Exception as e:
            logger.error(f"❌ DailyRanks 진단 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.report["sections"]["daily_ranks"] = {"error": str(e)}
    
    async def _diagnose_scraping_logs(self):
        """Step 6: 스크래핑 로그"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 6️⃣ : 스크래핑 로그")
        logger.info("="*80)
        
        try:
            from app.models.models import RawScrapingLog
            
            logs = self.db.query(RawScrapingLog).all()
            
            logger.info(f"\n✅ 총 스크래핑 로그: {len(logs)}")
            
            if logs:
                recent = sorted(logs, key=lambda x: x.captured_at, reverse=True)[:3]
                logger.info("\n최근 스크래핑 로그:")
                
                for log in recent:
                    logger.info(f"\n  🌐 Platform: {log.platform}")
                    logger.info(f"     ├─ Keyword: {log.keyword}")
                    logger.info(f"     └─ Captured: {log.captured_at}")
            else:
                logger.warning("⚠️  스크래핑 로그가 없습니다!")
            
            self.report["sections"]["scraping_logs"] = {
                "count": len(logs)
            }
        
        except Exception as e:
            logger.error(f"❌ 스크래핑 로그 진단 실패: {e}")
            self.report["sections"]["scraping_logs"] = {"error": str(e)}
    
    async def _diagnose_analytics_cache(self):
        """Step 7: API 응답 캐시"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 7️⃣ : Analytics Cache")
        logger.info("="*80)
        
        try:
            from app.models.models import AnalyticsCache
            
            cache = self.db.query(AnalyticsCache).all()
            
            logger.info(f"\n✅ 총 캐시 엔트리: {len(cache)}")
            
            if cache:
                logger.info("\n캐시 샘플:")
                for c in cache[:3]:
                    logger.info(f"  🔑 {c.cache_key}")
            else:
                logger.warning("⚠️  캐시가 없습니다!")
            
            self.report["sections"]["analytics_cache"] = {
                "count": len(cache)
            }
        
        except Exception as e:
            logger.error(f"❌ 캐시 진단 실패: {e}")
            self.report["sections"]["analytics_cache"] = {"error": str(e)}
    
    async def _diagnose_analysis_history(self):
        """Step 8: AnalysisHistory"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 8️⃣ : Analysis History")
        logger.info("="*80)
        
        try:
            from app.models.models import AnalysisHistory
            
            history = self.db.query(AnalysisHistory).all()
            
            logger.info(f"\n✅ 총 Analysis History: {len(history)}")
            
            if history:
                logger.info("\n최근 분석:")
                for h in sorted(history, key=lambda x: x.created_at, reverse=True)[:3]:
                    logger.info(f"\n  🔎 Keyword: {h.keyword} ({h.platform})")
                    logger.info(f"     ├─ Is Saved: {h.is_saved}")
                    logger.info(f"     └─ Created: {h.created_at}")
            else:
                logger.warning("⚠️  분석 기록이 없습니다!")
            
            self.report["sections"]["analysis_history"] = {
                "count": len(history)
            }
        
        except Exception as e:
            logger.error(f"❌ 분석 기록 진단 실패: {e}")
            self.report["sections"]["analysis_history"] = {"error": str(e)}
    
    async def _trace_data_flow(self):
        """Step 9: 데이터 흐름 추적"""
        
        logger.info("\n" + "="*80)
        logger.info("Step 9️⃣ : 데이터 흐름 추적")
        logger.info("="*80)
        
        from app.models.models import Client
        
        try:
            clients = self.db.query(Client).all()
            
            logger.info("\n📊 데이터 흐름 분석:")
            
            for client in clients[:3]:
                logger.info(f"\n🏥 Client: {client.name}")
                logger.info(f"   ├─ Keywords: {len(client.keywords)}")
                logger.info(f"   └─ DailyRanks: {len(client.daily_ranks)}")
            
            logger.info("\n" + "="*80)
            logger.info("✅ 진단 완료")
            logger.info("="*80)
        
        except Exception as e:
            logger.error(f"❌ 흐름 추적 실패: {e}")
        
        self.report["sections"]["data_flow"] = {"status": "completed"}
    
    def generate_summary(self):
        """진단 요약 생성"""
        
        logger.info("\n\n" + "="*80)
        logger.info("📋 진단 요약")
        logger.info("="*80)
        
        daily_ranks_count = self.report.get("sections", {}).get("daily_ranks", {}).get("count", 0)
        keywords_count = self.report.get("sections", {}).get("keywords", {}).get("count", 0)
        clients_count = self.report.get("sections", {}).get("clients", {}).get("count", 0)
        
        logger.info(f"\n📊 데이터 통계:")
        logger.info(f"  Clients: {clients_count}")
        logger.info(f"  Keywords: {keywords_count}")
        logger.info(f"  DailyRanks: {daily_ranks_count}")
        
        # 문제점 식별
        issues = []
        
        if daily_ranks_count == 0:
            issues.append("🔴 DailyRanks가 비어있음")
        
        if keywords_count == 0:
            issues.append("🔴 Keywords가 없음")
        
        if clients_count == 0:
            issues.append("🔴 Clients가 없음")
        
        if issues:
            logger.info(f"\n⚠️  발견된 문제:")
            for issue in issues:
                logger.info(f"  {issue}")
        else:
            logger.info(f"\n✅ 데이터 정상")
        
        self.report["issues"] = issues
        
        return self.report
