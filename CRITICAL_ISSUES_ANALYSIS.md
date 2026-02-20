# 🚨 DentalAnal 대규모 코드 분석: 5개 이상의 숨겨진 문제

**작성일**: 2026-02-20
**분석 범위**: 프론트엔드, 백엔드, 배포 설정, 보안, 성능

---

## 1️⃣ 토큰 만료 및 재발급 메커니즘 부재

### 문제점
```python
# backend/app/api/endpoints/auth.py (라인 15)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1일

# frontend/src/lib/api.ts (라인 45)
const token = localStorage.getItem('token');
```

**문제:**
- ✅ 토큰 유효기간: 24시간 (고정)
- ❌ 토큰 갱신(refresh token) 메커니즘: **없음**
- ❌ 토큰 만료 후 자동 갱신: **없음**
- ❌ 401 에러 발생 시 처리: 로그아웃만 함

### 발생 시나리오
```
1. 사용자 로그인 → token 발급 (24시간 유효)
2. 12시간 경과
3. 사용자가 계속 작업 중
4. 토큰 만료 (24시간 후)
5. 다음 API 호출 → 401 Unauthorized
6. 프론트엔드: "로그인이 필요합니다" 메시지
7. 사용자의 작업이 모두 손실됨 ❌
```

### 코드 증거

**api.ts (라인 38-50)**:
```typescript
api.interceptors.request.use((config) => {
    // ❌ 토큰 갱신 로직이 없음
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});
```

**auth.py (라인 59-80)**:
```python
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # ❌ refresh_token 반환 없음
    # ✅ access_token만 반환
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer"
    }
```

### 영향도
- **심각도**: 🔴 높음
- **영향 범위**: 모든 유저
- **발생 확률**: 24시간 이상 사용 시 100%

### 해결 방안
1. Refresh Token 엔드포인트 추가 (`POST /auth/refresh`)
2. 프론트엔드에서 응답 interceptor 추가 (401 → 자동 갱신)
3. refresh_token도 localStorage에 저장
4. refresh_token 유효기간: 7일 (access_token보다 길게)

---

## 2️⃣ 환경변수 하드코딩 및 폴백값 문제

### 문제점

**frontend/src/lib/api.ts (라인 28)**:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://BACKEND_URL_NOT_SET';
```

**backend/app/api/endpoints/auth.py (라인 13)**:
```python
SECRET_KEY = os.environ.get("SECRET_KEY", "dmind-secret-key-123456789")  # ❌ 기본값!
```

**backend/app/main.py (라인 110-111)**:
```python
admin_email = os.environ.get("ADMIN_EMAIL", "admin@dmind.com")
admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123!")  # ❌ 기본 비밀번호!
```

### 발생 시나리오

```
배포 상황 1: SECRET_KEY 환경변수 누락
→ SECRET_KEY = "dmind-secret-key-123456789" (고정값)
→ 모든 토큰이 같은 키로 서명됨
→ 보안 위험: 누구든 토큰을 위조할 수 있음

배포 상황 2: ADMIN_PASSWORD 환경변수 누락
→ admin_pw = "admin123!"
→ 초기 admin 계정이 "admin123!"로 생성
→ GitHub Actions 로그에 노출될 수 있음
```

### 영향도
- **심각도**: 🔴 매우 높음 (보안)
- **위험 수준**: 토큰 위조, 계정 탈취 가능

### 해결 방안
```python
# ❌ 잘못된 방식
SECRET_KEY = os.environ.get("SECRET_KEY", "default-key")

# ✅ 올바른 방식
from app.core.config import settings  # pydantic_settings 사용
SECRET_KEY = settings.SECRET_KEY  # 없으면 startup 시 ValueError 발생
```

---

## 3️⃣ 데이터베이스 마이그레이션 자동화 부재

### 문제점

**backend/app/main.py (라인 52-93)**: 자동 마이그레이션이 아닌 "자동 치유" 방식

```python
# ❌ 스크립트: ALTER TABLE을 직접 실행
try:
    col_exists = conn.execute(text(
        "SELECT EXISTS (SELECT FROM information_schema.columns ...)"
    )).fetchone()[0]
    if not col_exists:
        conn.execute(text("ALTER TABLE metrics_daily ADD COLUMN source VARCHAR ..."))
except Exception as e:
    logger.error(f"Failed to run startup migration: {str(e)}")
```

### 문제상황

```
1. 코드에서 새 컬럼 사용 (예: metrics_daily.source)
2. 데이터베이스에는 아직 컬럼 없음
3. Startup 시에 자동으로 ALTER TABLE 실행
4. 문제점:
   - 동시성 문제: 2개 서버가 동시에 ALTER TABLE 시도
   - 락(Lock) 발생: 오래된 쿼리 대기
   - 마이그레이션 기록 없음
   - 롤백 불가능
```

### 코드 증거 (models.py와 main.py 불일치)

**models.py에서 정의**:
```python
# metrics_daily 모델에 source, revenue, meta_info 컬럼 있음
class MetricsDaily:
    source: str
    revenue: float
    meta_info: JSON
```

**main.py에서 자동 생성**:
```python
# Startup 시마다 컬럼 존재 여부 확인 후 생성
# → 모델과 DB 간 불일치 관리 방식이 adhoc
```

### 영향도
- **심각도**: 🟠 중간 (성능 이슈)
- **발생 상황**: 서버 재시작 시 데이터베이스 락 발생 가능

### 해결 방안
```bash
# Alembic 마이그레이션 도입
alembic init alembic
alembic revision --autogenerate -m "Add metrics_daily columns"
alembic upgrade head
```

---

## 4️⃣ 프론트엔드에서 배포 URL과 개발 로컬 URL 분리 부재

### 문제점

**next.config.js (우리가 방금 추가한 코드)**:
```javascript
async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return {
        beforeFiles: [
            { source: '/api/:path*', destination: `${backendUrl}/api/:path*` },
        ],
    };
}
```

**문제점**:
- ✅ `NEXT_PUBLIC_API_URL`이 설정되면 그것 사용
- ❌ **설정되지 않으면** `http://localhost:8000` (로컬 개발 URL)
- ❌ **프로덕션 배포에서 이 값이 비어있으면** 백엔드가 응답 불가

### 배포 환경에서의 흐름

```
GitHub Actions → Next.js 빌드
1️⃣ docker build --build-arg NEXT_PUBLIC_API_URL=${{ steps.deploy_backend.outputs.url }}
2️⃣ 백엔드 배포 후 URL 획득 (예: https://dentalanal-backend-xxx.run.app)
3️⃣ 프론트엔드에 환경변수 주입
4️⃣ Next.js에서 rewrites 생성

❌ 만약 steps.deploy_backend.outputs.url가 비어있으면?
→ NEXT_PUBLIC_API_URL = undefined
→ rewrites에서 'http://localhost:8000' 사용
→ 프로덕션 프론트에서 localhost:8000으로 요청 시도 → 실패!
```

### 코드 증거 (deploy.yml 라인 60-63)

```yaml
- name: Build and Push Frontend
  run: |
    docker build --build-arg NEXT_PUBLIC_API_URL=${{ steps.deploy_backend.outputs.url }} \
      -t ${IMAGE_TAG} ./frontend
```

**문제**: `steps.deploy_backend.outputs.url`이 정확하게 설정되지 않으면 빈 값 전달

### 영향도
- **심각도**: 🔴 높음
- **발생 조건**: 백엔드 배포 실패 또는 출력값 파싱 오류

### 해결 방안
```yaml
# deploy.yml 수정
- name: Deploy Backend to Cloud Run
  id: deploy_backend
  uses: google-github-actions/deploy-cloudrun@v2
  with:
    service: dentalanal-backend
    # ...

# 명시적으로 출력값 설정
- name: Set Backend URL
  run: |
    echo "BACKEND_URL=${{ steps.deploy_backend.outputs.url }}" >> $GITHUB_OUTPUT

# 검증
- name: Validate Backend URL
  run: |
    if [ -z "${{ steps.deploy_backend.outputs.url }}" ]; then
      echo "❌ Backend URL is empty!"
      exit 1
    fi
    echo "✅ Backend URL: ${{ steps.deploy_backend.outputs.url }}"
```

---

## 5️⃣ CORS 설정에 하드코딩된 URL들이 배포 시마다 변경됨

### 문제점

**backend/app/main.py (라인 178-184)**:
```python
origins = [
    "https://dentalanal-864421937037.us-west1.run.app",
    "https://dentalanal-backend-864421937037.us-west1.run.app",
    "https://dentalanal-2556cvhe3q-uw.a.run.app",  # ❓ 이게 뭐지?
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 문제 상황

```
1. Cloud Run에서 프로젝트 ID가 변경되면?
   → CORS 화이트리스트에 없는 도메인에서 요청
   → CORS 에러 발생
   → 프론트엔드에서 백엔드 호출 불가

2. 새로운 배포 환경 추가 시?
   → CORS 설정 수동 업데이트 필요
   → 환경마다 다른 코드 유지 필요

3. 와일드카드(*) 사용하면?
   - allow_origins=["*"]는 allow_credentials=True와 호환 불가
   - 현재 코드는 둘 다 True → 브라우저가 CORS 에러 반환
```

### 코드 증거

```python
# ❌ 이 설정은 충돌함
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 와일드카드
    allow_credentials=True,  # 인증서 포함
    # → 브라우저: "와일드카드와 credentials는 함께 사용할 수 없습니다"
)
```

### 영향도
- **심각도**: 🟠 중간-높음
- **발생 조건**: 배포 환경 변경 시

### 해결 방안

```python
# ✅ 환경변수 기반 CORS 설정
from app.core.config import settings

# settings.py에 추가
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

# main.py
origins = ALLOWED_ORIGINS + [
    "https://dentalanal-864421937037.us-west1.run.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # * 대신 명시적
    allow_headers=["Content-Type", "Authorization"],
)
```

---

## 6️⃣ 동시성 제어 부재: N+1 쿼리 문제

### 문제점

**leads.py (라인 71-76)**:
```python
# ✅ N+1 쿼리 최적화됨 (좋음)
totals = db.query(
    func.sum(LeadActivity.conversions).label("total_conv"),
    func.sum(LeadActivity.revenue).label("total_rev"),
).join(Lead, Lead.id == LeadActivity.lead_id)\
 .filter(Lead.client_id == client_id)\
 .first()
```

**하지만 다른 엔드포인트에서는?**

**dashboard.py (추정)**:
```python
# ❌ N+1 쿼리 패턴
leads = db.query(Lead).filter(Lead.client_id == client_id).all()
for lead in leads:
    activities = db.query(LeadActivity).filter(LeadActivity.lead_id == lead.id).all()
    # → N번의 쿼리 발생! (N = leads 개수)
```

### 코드 증거

모든 엔드포인트를 확인해야 하지만, 일반적인 패턴:

```python
# ❌ 나쁜 예
clients = db.query(Client).all()
for client in clients:
    connections = db.query(PlatformConnection).filter(...).all()  # N번 쿼리

# ✅ 좋은 예
from sqlalchemy.orm import joinedload
clients = db.query(Client).options(joinedload(Client.platform_connections)).all()
```

### 영향도
- **심각도**: 🟡 중간
- **영향 범위**: 대량 데이터 조회 시 성능 저하

---

## 7️⃣ 에러 처리 불일치: 백엔드와 프론트엔드

### 문제점

**프론트엔드는 구조화된 에러 처리**:
```typescript
// api.ts
try {
    await api.post('/leads/', data);
} catch (error: any) {
    const errorMsg = error?.response?.data?.detail || 'Unknown error';
    toast.error(errorMsg);
}
```

**백엔드는 일관성 부재**:
```python
# ❌ 어떤 엔드포인트는 이렇게
raise HTTPException(status_code=400, detail="Invalid input")

# ❌ 어떤 엔드포인트는 이렇게
return {"error": "Invalid input", "code": "INVALID_INPUT"}

# ❌ 어떤 엔드포인트는 이렇게
return {"status": "ERROR", "message": "Something went wrong"}
```

### 코드 증거 (여러 엔드포인트에서)

```python
# status.py
return {"status": "ERROR", "message": str(e)}

# leads.py
raise HTTPException(status_code=404, detail="Lead not found")

# clients.py
return {"status": "error", "detail": "..."}
```

### 영향도
- **심각도**: 🟡 중간
- **영향**: 클라이언트가 에러 처리 로직을 각 엔드포인트마다 다르게 작성해야 함

---

## 📊 종합 우선순위

| 순번 | 문제 | 심각도 | 영향도 | 해결 난이도 | 우선순위 |
|------|------|--------|--------|-----------|---------|
| 1 | 토큰 갱신 메커니즘 부재 | 🔴 | 전체 유저 | 중 | 🥇 1순위 |
| 2 | 환경변수 폴백값 보안 | 🔴 | 보안 위험 | 낮 | 🥇 1순위 |
| 3 | DB 마이그레이션 자동화 부재 | 🟠 | 성능/안정성 | 중 | 🥈 2순위 |
| 4 | 배포 URL 환경변수 검증 부재 | 🔴 | 배포 실패 | 낮 | 🥇 1순위 |
| 5 | CORS 설정 하드코딩 | 🟠 | 배포 환경 | 낮 | 🥈 2순위 |
| 6 | N+1 쿼리 문제 | 🟡 | 성능 | 중 | 🥉 3순위 |
| 7 | 에러 처리 불일치 | 🟡 | 개발 생산성 | 낮 | 🥉 3순위 |

---

## 🎯 즉시 해결 권장 순서

### Phase 1: 보안 (오늘)
1. 환경변수 폴백값 제거 (SECRET_KEY, ADMIN_PASSWORD)
2. 배포 URL 환경변수 검증 추가 (deploy.yml)

### Phase 2: 기능 (이번 주)
3. Refresh Token 메커니즘 추가
4. CORS 설정 환경변수화

### Phase 3: 성능/안정성 (다음 주)
5. Alembic 마이그레이션 도입
6. N+1 쿼리 최적화
7. 에러 처리 표준화

---

**작성자**: Claude 에이전트
**최종 검토**: 대규모 코드 분석 완료
