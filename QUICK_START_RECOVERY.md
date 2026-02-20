# ⚡ 빠른 데이터 복구 가이드 (Quick Start)

> **상황**: DentalAnal 데이터가 들어오지 않음
> **원인**: 디버그 라우터 미배포
> **상태**: 🟡 Cloud Run 배포 진행 중 (5-10분)

---

## 🚀 지금 할 일 (3단계)

### Step 1️⃣: 배포 완료 대기 (5-10분)
```bash
# 터미널에서 실시간 로그 확인
gcloud run logs read --service dentalanal --region us-west1 -f

# 또는 다시 시도:
# https://dentalanal-864421937037.us-west1.run.app/api/v1/debug/stats
# → 200 응답이면 배포 완료!
```

### Step 2️⃣: 데이터 현황 진단 (배포 완료 후)

브라우저 콘솔 (F12)에서:
```javascript
fetch('/api/v1/debug/stats')
  .then(r => r.json())
  .then(d => console.log(JSON.stringify(d.data, null, 2)))
```

**기대 결과**:
```json
{
  "clients": 1,
  "keywords": 1,
  "daily_ranks": 5,
  "analysis_history": 1
}
```

### Step 3️⃣: 결과에 따른 조치

| 결과 | 의미 | 조치 |
|------|------|------|
| ✅ daily_ranks > 0 | 데이터 정상 흐르는 중 | 축하! 완료 |
| ❌ daily_ranks = 0 | 스크래핑 미작동 | [상세 가이드](#-상세-진단) 참고 |
| ⚠️ clients = 0 | 테스트 환경 | 테스트 데이터 생성 (아래) |

---

## 🧪 테스트 데이터 생성 (필요시)

```javascript
fetch('/api/v1/status/dev/seed-test-data', { method: 'POST' })
  .then(r => r.json())
  .then(d => console.log('생성됨:', d))
```

응답:
```json
{
  "status": "success",
  "client_id": "...",
  "keywords_created": ["임플란트", "치아교정"],
  "daily_ranks_created": 10
}
```

그 후 다시 `/api/v1/debug/stats` 호출하면 `daily_ranks: 10`으로 증가!

---

## 📊 상세 진단

### Scenario A: daily_ranks = 0 (가장 흔함)

**원인**: 스크래핑 실패

**진단**:
```javascript
// 키워드 추적
fetch('/api/v1/debug/trace-keyword/임플란트')
  .then(r => r.json())
  .then(d => console.log(d.data))
```

**Cloud Run 로그 확인**:
```bash
gcloud run logs read --limit 500 | grep -i "scrape\|error\|failed"
```

**로그에서 찾을 것**:
- ✅ `[Scraper] Scraped rank=5` → 정상
- ❌ `[ERROR] Timeout` → timeout 증가 필요
- ❌ `[ERROR] Connection refused` → 네트워크 문제
- ❌ `[ERROR] Memory exceeded` → 메모리 부족

---

### Scenario B: keywords = 0 (SetupWizard 미사용)

**조치**: SetupWizard에서 새 조사 시작

1. 좌측 메뉴 → "새 조사 시작" 또는 설정
2. 키워드 입력: "임플란트"
3. 플랫폼: "Naver Search"
4. "조사시작" 클릭
5. 5-30초 대기

---

### Scenario C: clients = 0 (순수 테스트 환경)

**조치**: 테스트 데이터 생성
```javascript
fetch('/api/v1/status/dev/seed-test-data', { method: 'POST' })
```

완료 후 다시 시작!

---

## 🔧 긴급 패치 (문제 지속 시)

### 만약 Timeout 에러
```python
# backend/app/scrapers/base.py 수정
TIMEOUT = 180  # 60에서 180으로 변경
```

배포:
```bash
git add backend/app/scrapers/base.py
git commit -m "[Hotfix] 스크래핑 타임아웃 증가"
git push origin main
```

### 만약 메모리 에러
```bash
gcloud run deploy dentalanal-service \
  --memory 2Gi \
  --region us-west1
```

---

## ✅ 성공 신호

다음 중 하나라도 보이면 ✅:
```
1. /api/v1/debug/stats에서 daily_ranks > 0
2. 대시보드에 데이터 차트 표시
3. SetupWizard 후 5초 내 UI 업데이트
4. 클라우드 로그에 "[Scraper] Saved DailyRank"
```

---

## 📞 참고

| 문서 | 내용 |
|------|------|
| **DEPLOYMENT_TROUBLESHOOTING_GUIDE.md** | 상세 진단 (3단계, 문제별 해결) |
| **URGENT_ACTION_PLAN.md** | 시간순 액션 항목 (20분 타임라인) |
| **DIAGNOSIS_AND_RECOVERY_SUMMARY.md** | 전체 상황 요약 (기술 상세) |

---

## 🎯 체크리스트

- [ ] Cloud Run 배포 완료 확인
- [ ] /api/v1/debug/stats 호출 성공
- [ ] 데이터 현황 확인 (daily_ranks 값)
- [ ] 필요시 테스트 데이터 생성
- [ ] 필요시 긴급 패치 적용
- [ ] SetupWizard 재테스트
- [ ] 대시보드 데이터 표시 확인

---

**최종 목표**: daily_ranks > 0 + 대시보드에 데이터 표시

**예상 완료 시각**: 2026-02-21 18:00 KST

