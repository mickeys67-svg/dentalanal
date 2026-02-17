#!/usr/bin/env python3
"""Full feature test after deployment"""
import requests
import json
import sys

BASE_URL = 'https://dentalanal-backend-864421937037.us-west1.run.app'

print("=" * 80)
print("DentalAnal Full Feature Test - Post Deployment")
print("=" * 80)

# Login
print("\n[AUTH] Logging in...")
try:
    login_resp = requests.post(
        f'{BASE_URL}/api/v1/auth/login',
        data={'username': 'admin@dmind.com', 'password': 'admin123!'},
        timeout=10
    )
    if login_resp.status_code != 200:
        print("[FAIL] Login failed")
        sys.exit(1)
    token = login_resp.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    print("[OK] Logged in successfully")
except Exception as e:
    print("[ERROR] {}".format(e))
    sys.exit(1)

# Test Phase 5 - Reports
print("\n[PHASE 5] Report Management Features:")
print("  " + "-" * 70)

try:
    # Test 1: GET all reports
    print("  1. GET /api/v1/reports (NEW ENDPOINT)")
    resp = requests.get(
        f'{BASE_URL}/api/v1/reports',
        headers=headers,
        timeout=10
    )
    if resp.status_code == 200:
        reports = resp.json()
        print("     [OK] Status 200")
        print("     Total reports: {}".format(len(reports)))
    else:
        print("     [FAIL] Status {}".format(resp.status_code))

    # Test 2: Get templates
    print("\n  2. GET /api/v1/reports/templates")
    resp = requests.get(
        f'{BASE_URL}/api/v1/reports/templates',
        headers=headers,
        timeout=10
    )
    if resp.status_code == 200:
        templates = resp.json()
        print("     [OK] Status 200")
        print("     Total templates: {}".format(len(templates)))
        if templates:
            print("     - {}".format(templates[0].get('name')))
    else:
        print("     [FAIL] Status {}".format(resp.status_code))

    # Test 3: Check for PDF endpoint
    print("\n  3. GET /api/v1/reports/pdf/{report_id} (Phase 5 Part 3)")
    resp = requests.get(
        f'{BASE_URL}/api/v1/reports/pdf/00000000-0000-0000-0000-000000000000',
        headers=headers,
        timeout=10
    )
    if resp.status_code == 404 and 'not found' in resp.text.lower():
        print("     [PENDING] Endpoint not yet deployed (expected)")
    else:
        print("     [Status] {}".format(resp.status_code))

except Exception as e:
    print("     [ERROR] {}".format(e))

# Test Phase 4 - Competitors
print("\n[PHASE 4] Competitor Intelligence:")
print("  " + "-" * 70)

try:
    # Test 1: Competitors endpoint
    print("  1. GET /api/v1/analyze/competitors (NEW ENDPOINT)")
    resp = requests.post(
        f'{BASE_URL}/api/v1/analyze/competitors',
        json={
            'keyword': 'implant',
            'platform': 'NAVER_PLACE',
            'top_n': 5
        },
        headers=headers,
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        print("     [OK] Status 200")
        print("     Response keys: {}".format(list(data.keys())[:3]))
    else:
        print("     [Status] {}".format(resp.status_code))

    # Test 2: Check for ROI endpoint
    print("\n  2. GET /api/v1/roi/* (Phase 4 Part 2)")
    resp = requests.get(
        f'{BASE_URL}/api/v1/roi/summary',
        headers=headers,
        timeout=10
    )
    if resp.status_code == 404:
        print("     [PENDING] Endpoint not yet deployed")
    elif resp.status_code == 200:
        print("     [OK] Status 200")
    else:
        print("     [Status] {}".format(resp.status_code))

    # Test 3: Check for Trends endpoint
    print("\n  3. GET /api/v1/trends/* (Phase 4 Part 3)")
    resp = requests.get(
        f'{BASE_URL}/api/v1/trends/analysis',
        headers=headers,
        timeout=10
    )
    if resp.status_code == 404:
        print("     [PENDING] Endpoint not yet deployed")
    elif resp.status_code == 200:
        print("     [OK] Status 200")
    else:
        print("     [Status] {}".format(resp.status_code))

except Exception as e:
    print("     [ERROR] {}".format(e))

# Test System Health
print("\n[HEALTH] System Status:")
print("  " + "-" * 70)

try:
    resp = requests.get(
        f'{BASE_URL}/api/v1/status/status',
        timeout=10
    )
    if resp.status_code == 200:
        status = resp.json()
        print("  Status: {}".format(status.get('status')))
        print("  Database: {}".format(status.get('database')))
        print("  Scheduler: {}".format(status.get('scheduler')))
        print("  Uptime: {}".format(status.get('uptime')))
    else:
        print("  [ERROR] Status {}".format(resp.status_code))
except Exception as e:
    print("  [ERROR] {}".format(e))

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
