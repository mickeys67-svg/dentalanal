#!/usr/bin/env python3
"""Analyze backend bugs and data flow issues"""
import requests
import json
import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

BASE_URL = 'https://dentalanal-backend-864421937037.us-west1.run.app'

print("=" * 80)
print("DentalAnal Backend Bug Analysis")
print("=" * 80)

# Get auth token
print("\n[STEP 1] Getting authentication token...")
try:
    login_resp = requests.post(
        f'{BASE_URL}/api/v1/auth/login',
        data={'username': 'admin@dmind.com', 'password': 'admin123!'},
        timeout=10
    )
    if login_resp.status_code != 200:
        print("[FAIL] Login failed: {}".format(login_resp.status_code))
        sys.exit(1)
    token = login_resp.json().get('access_token')
    headers = {'Authorization': 'Bearer {}'.format(token)}
    print("[OK] Authenticated")
except Exception as e:
    print("[FAIL] {}".format(e))
    sys.exit(1)

# Test 1: Check API Endpoints
print("\n[TEST 1] Checking API Endpoints...")
endpoints = [
    ('/api/v1/clients/', 'Clients'),
    ('/api/v1/dashboard/summary', 'Dashboard'),
    ('/api/v1/reports/templates', 'Report Templates'),
    ('/api/v1/analyze/competitors', 'Competitors - POST'),
    ('/api/v1/status/status', 'Health Status'),
]

for endpoint, name in endpoints:
    try:
        resp = requests.get(
            f'{BASE_URL}{endpoint}',
            headers=headers,
            timeout=5
        )
        status = "[OK]" if resp.status_code in [200, 400, 401] else "[FAIL]"
        print("{} {} - Status: {}".format(status, name, resp.status_code))
    except Exception as e:
        print("[ERROR] {} - {}".format(name, str(e)[:50]))

# Test 2: Check Phase 5 endpoints
print("\n[TEST 2] Checking Phase 5 Endpoints...")
phase5_endpoints = [
    ('/api/v1/reports', 'Get Reports'),
    ('/api/v1/reports/templates', 'Get Templates'),
]

for endpoint, name in phase5_endpoints:
    try:
        resp = requests.get(
            f'{BASE_URL}{endpoint}',
            headers=headers,
            timeout=5
        )
        print("[{}] {} - Status: {}".format(
            "OK" if resp.status_code == 200 else "WARN",
            name,
            resp.status_code
        ))
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print("      Items: {}".format(len(data)))
            else:
                print("      Response: {}".format(str(data)[:100]))
    except Exception as e:
        print("[ERROR] {} - {}".format(name, str(e)[:50]))

# Test 3: Check data availability
print("\n[TEST 3] Checking Data Availability...")
print("\n  A. Clients:")
try:
    resp = requests.get(f'{BASE_URL}/api/v1/clients/', headers=headers, timeout=5)
    if resp.status_code == 200:
        clients = resp.json()
        print("     Total: {}".format(len(clients)))
        if not clients:
            print("     WARNING: No clients found!")
    else:
        print("     ERROR: Status {}".format(resp.status_code))
except Exception as e:
    print("     ERROR: {}".format(e))

print("\n  B. Keywords:")
try:
    resp = requests.get(f'{BASE_URL}/api/v1/analyze/targets/search', headers=headers, timeout=5)
    if resp.status_code == 200:
        keywords = resp.json()
        print("     Total: {}".format(len(keywords) if isinstance(keywords, list) else 0))
    else:
        print("     ERROR: Status {}".format(resp.status_code))
except Exception as e:
    print("     ERROR: {}".format(e))

print("\n  C. Report Templates:")
try:
    resp = requests.get(f'{BASE_URL}/api/v1/reports/templates', headers=headers, timeout=5)
    if resp.status_code == 200:
        templates = resp.json()
        print("     Total: {}".format(len(templates)))
        for i, tmpl in enumerate(templates[:3]):
            print("     - {}".format(tmpl.get('name', 'N/A')))
    else:
        print("     ERROR: Status {}".format(resp.status_code))
except Exception as e:
    print("     ERROR: {}".format(e))

# Test 4: Database health check
print("\n[TEST 4] Database Health...")
try:
    resp = requests.get(f'{BASE_URL}/api/v1/status/status', timeout=5)
    if resp.status_code == 200:
        status = resp.json()
        print("  Status: {}".format(status.get('status')))
        print("  Database: {}".format(status.get('database')))
        print("  Scheduler: {}".format(status.get('scheduler')))

        logs = status.get('recent_logs', [])
        print("\n  Recent Logs:")
        for log in logs[:3]:
            msg = log.get('message', '')
            level = log.get('level', 'INFO')
            print("  [{:5s}] {}".format(level, msg[:70]))
    else:
        print("  ERROR: Status {}".format(resp.status_code))
except Exception as e:
    print("  ERROR: {}".format(e))

print("\n" + "=" * 80)
print("Analysis Complete!")
print("=" * 80)
