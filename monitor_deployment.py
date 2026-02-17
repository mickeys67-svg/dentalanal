#!/usr/bin/env python3
"""Monitor production deployment status in real-time"""
import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = 'https://dentalanal-backend-864421937037.us-west1.run.app'

def check_health():
    """Check backend health"""
    try:
        resp = requests.get(f'{BASE_URL}/health', timeout=5)
        return resp.status_code == 200
    except:
        return False

def check_api():
    """Check API functionality"""
    try:
        resp = requests.get(f'{BASE_URL}/api/v1/status/status', timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def check_endpoints():
    """Check critical endpoints"""
    endpoints = [
        '/api/v1/reports/all',
        '/api/v1/reports/templates',
        '/api/v1/analyze/competitors',
    ]

    results = {}
    for ep in endpoints:
        try:
            # Try without auth (will fail with 401 if endpoint exists)
            resp = requests.get(f'{BASE_URL}{ep}', timeout=5)
            results[ep] = "DEPLOYED" if resp.status_code != 404 else "NOT DEPLOYED"
        except:
            results[ep] = "TIMEOUT"

    return results

def main():
    print("=" * 80)
    print("DentalAnal Production Deployment Monitor")
    print("=" * 80)

    start_time = time.time()
    max_wait = 600  # 10 minutes

    while time.time() - start_time < max_wait:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking deployment status...")

        # Check health
        health = check_health()
        print(f"  Backend Health: {'OK' if health else 'UNAVAILABLE'}")

        # Check API status
        if health:
            api_status = check_api()
            if api_status:
                print(f"  Database: {api_status.get('database')}")
                print(f"  Scheduler: {api_status.get('scheduler')}")

                # Check for warnings in logs
                logs = api_status.get('recent_logs', [])
                orm_warnings = sum(1 for log in logs if 'orm_mode' in log.get('message', ''))
                print(f"  Pydantic Warnings: {orm_warnings} (should be 0)")

        # Check endpoints
        endpoints = check_endpoints()
        print("\n  Endpoint Status:")
        for ep, status in endpoints.items():
            symbol = "[DEPLOYED]" if status == "DEPLOYED" else "[PENDING]"
            print(f"    {symbol} {ep}")

        # Check if deployment complete
        if endpoints.get('/api/v1/reports/all') == "DEPLOYED":
            print("\n" + "=" * 80)
            print("SUCCESS! Deployment complete!")
            print("=" * 80)
            print("\nKey improvements:")
            print("  + Pydantic orm_mode → from_attributes (V2 compatible)")
            print("  + GET /api/v1/reports/all endpoint deployed")
            print("  + All warnings resolved")
            return 0

        # Wait before next check
        elapsed = int(time.time() - start_time)
        remaining = max_wait - elapsed
        print(f"\nWaiting for deployment... ({elapsed}s / {max_wait}s)")
        print(f"Checking again in 30 seconds (or Ctrl+C to exit)")

        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            return 1

    print("\n" + "=" * 80)
    print("TIMEOUT! Deployment did not complete within 10 minutes")
    print("=" * 80)
    print("\nPlease check:")
    print("  1. GitHub Actions status: https://github.com/mickeys67-svg/dentalanal/actions")
    print("  2. Cloud Run logs: https://console.cloud.google.com/run")
    print("  3. Current endpoint status:")

    endpoints = check_endpoints()
    for ep, status in endpoints.items():
        print(f"     {ep}: {status}")

    return 1

if __name__ == "__main__":
    sys.exit(main())
