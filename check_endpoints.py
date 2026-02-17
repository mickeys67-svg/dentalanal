#!/usr/bin/env python3
"""Check what endpoints are deployed"""
import requests
import json

try:
    r = requests.get(
        'https://dentalanal-backend-864421937037.us-west1.run.app/openapi.json',
        timeout=10
    )

    if r.status_code == 200:
        openapi = r.json()
        paths = list(openapi['paths'].keys())

        # Check for specific endpoints
        checks = [
            ('/api/v1/reports', 'GET /reports (all)'),
            ('/api/v1/reports/{client_id}', 'GET /reports/{client_id}'),
            ('/api/v1/reports/detail/{report_id}', 'GET /reports/detail'),
            ('/api/v1/reports/pdf/{report_id}', 'GET /reports/pdf'),
            ('/api/v1/analyze/competitors', 'GET /competitors'),
            ('/api/v1/competitors', 'GET /competitors (alt)'),
            ('/api/v1/roi', 'GET /roi'),
            ('/api/v1/trends', 'GET /trends'),
        ]

        print("=" * 70)
        print("DentalAnal Production Endpoint Status")
        print("=" * 70)

        for endpoint, desc in checks:
            status = "DEPLOYED" if endpoint in paths else "NOT DEPLOYED"
            symbol = "[OK]" if status == "DEPLOYED" else "[FAIL]"
            print("{} {} - {}".format(symbol, endpoint, status))

        print("\n" + "=" * 70)
        print("All Report-related Endpoints:")
        print("=" * 70)
        report_endpoints = sorted([p for p in paths if 'report' in p.lower()])
        for ep in report_endpoints:
            print("  {}".format(ep))

    else:
        print("ERROR: {}".format(r.status_code))

except Exception as e:
    print("ERROR: {}".format(e))
