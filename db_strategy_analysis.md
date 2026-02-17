# Database Strategy Analysis (Supabase vs. Alternatives)

## 1. Current Situation Analysis
*   **Provider**: Supabase (Remote PostgreSQL)
*   **Connection Mode**: Transaction Pooler (Port 6543)
*   **Issues Observed**:
    1.  **DNS Resolution Failure**: `db.xklppnykoeezgtxmomrl.supabase.co` 도메인 해석 intermittently 실패.
    2.  **IPv6 Sensitivity**: 로컬 환경에서 IPv6 관련 라우팅 문제 발생.
    3.  **Network Latency**: 모든 API 요청과 스크래핑 결과 저장이 원격지로 전송되므로 E2E 테스트 시 물리적 지연 발생.

## 2. Comparison Table

| Feature | Supabase (Pooler 6543) | Supabase (Direct 5432) | Local PostgreSQL (Docker) | SQLite (Local) |
| :--- | :--- | :--- | :--- | :--- |
| **Stability** | Low (Sensitive to DNS/ISP) | Medium (Standard TCP) | **High** (No Network) | **High** (No Network) |
| **Performance** | High Latency | Medium Latency | **Zero Latency** | **Zero Latency** |
| **Maintenance** | **Zero** (Managed) | **Zero** (Managed) | Low (Local setup) | **Zero** (Single file) |
| **Scaling** | Excellent | Good | Manual | Limited |
| **Prod suitability** | High (Serverless friendly) | High | Medium (DIY) | Low |

## 3. Recommended Approach: "Hybrid Strategy"

### A. Local Development & E2E Testing
*   **Recommendation**: **SQLite** (단기 테스트용) 또는 **Local PostgreSQL** (중장기).
*   **Reason**: 네트워크 의존성을 제거하여 `verify_critical_flows.py` 실행 시 1초 이내에 결과를 확인할 수 있도록 함. 현재 발생 중인 DNS 오류로부터 완전히 자유로움.

### B. Production Environment (Cloud Run)
*   **Recommendation**: **Supabase Direct Connection (Port 5432)**.
*   **Reason**: Cloud Run은 이미 원격지 서버이므로 관리형 서비스(Supabase)를 그대로 쓰되, 안정성이 떨어지는 Pooler(6543) 대신 표준 포트(5432)를 사용. 

## 4. Immediate Action Item
1.  **Local Test**: `.env`의 `DATABASE_URL`을 `sqlite:///./test.db`로 잠시 변경하여 백엔드 기능 자체에 결함이 없는지 1차 검증.
2.  **Supabase Fix**: 원격 DB를 꼭 써야 한다면 호스트명을 IPv4 IP로 하드코딩하거나, 5432 포트로 전환.
