#!/usr/bin/env python3
"""Test backend API data flow"""
import requests
import json
import sys
import os

# Force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

BASE_URL = 'https://dentalanal-backend-864421937037.us-west1.run.app'

print("=" * 80)
print("DentalAnal Backend Data Flow Test")
print("=" * 80)

# 1. Test Login
print("\n[1] Testing login...")
try:
    login_resp = requests.post(
        f'{BASE_URL}/api/v1/auth/login',
        data={'username': 'admin@dmind.com', 'password': 'admin123!'},
        timeout=10
    )
    if login_resp.status_code == 200:
        token = login_resp.json().get('access_token')
        print("[OK] Login successful")
        print("   Token: {}...".format(token[:20]))
    else:
        print("[FAIL] Login failed: {}".format(login_resp.status_code))
        print("   Response: {}".format(login_resp.text))
        sys.exit(1)
except Exception as e:
    print("[FAIL] Login error: {}".format(e))
    sys.exit(1)

# 2. Test Clients API
print("\n[2] Testing clients API...")
try:
    headers = {'Authorization': 'Bearer {}'.format(token)}
    clients_resp = requests.get(
        f'{BASE_URL}/api/v1/clients/',
        headers=headers,
        timeout=10
    )
    if clients_resp.status_code == 200:
        clients = clients_resp.json()
        print("[OK] Clients fetched: {} clients found".format(len(clients)))
        if clients:
            print("   First client: {}".format(clients[0].get('name', 'N/A')))
    else:
        print("[FAIL] Clients API failed: {}".format(clients_resp.status_code))
        print("   Response: {}".format(clients_resp.text[:200]))
except Exception as e:
    print("[FAIL] Clients error: {}".format(e))

# 3. Test Dashboard Summary
print("\n[3] Testing dashboard API...")
try:
    dashboard_resp = requests.get(
        f'{BASE_URL}/api/v1/dashboard/summary',
        headers=headers,
        timeout=10
    )
    if dashboard_resp.status_code == 200:
        data = dashboard_resp.json()
        print("[OK] Dashboard data fetched")
        print("   KPIs: {} items".format(len(data.get('kpis', []))))
        print("   Campaigns: {} items".format(len(data.get('campaigns', []))))
        print("   Is sample: {}".format(data.get('is_sample', False)))
    else:
        print("[FAIL] Dashboard API failed: {}".format(dashboard_resp.status_code))
except Exception as e:
    print("[FAIL] Dashboard error: {}".format(e))

# 4. Test Report Templates
print("\n[4] Testing report templates API...")
try:
    templates_resp = requests.get(
        f'{BASE_URL}/api/v1/reports/templates',
        headers=headers,
        timeout=10
    )
    if templates_resp.status_code == 200:
        templates = templates_resp.json()
        print("[OK] Report templates fetched: {} templates found".format(len(templates)))
        if templates:
            print("   First template: {}".format(templates[0].get('name', 'N/A')))
    else:
        print("[FAIL] Templates API failed: {}".format(templates_resp.status_code))
        print("   Response: {}".format(templates_resp.text[:200]))
except Exception as e:
    print("[FAIL] Templates error: {}".format(e))

# 5. Test Status Endpoint
print("\n[5] Testing health status...")
try:
    status_resp = requests.get(
        f'{BASE_URL}/api/v1/status/status',
        timeout=10
    )
    if status_resp.status_code == 200:
        status = status_resp.json()
        print("[OK] Status: {}".format(status.get('status')))
        print("   Database: {}".format(status.get('database')))
        print("   Scheduler: {}".format(status.get('scheduler')))
        print("   Uptime: {}".format(status.get('uptime')))
    else:
        print("[FAIL] Status API failed: {}".format(status_resp.status_code))
except Exception as e:
    print("[FAIL] Status error: {}".format(e))

print("\n" + "=" * 80)
print("Test completed!")
print("=" * 80)
