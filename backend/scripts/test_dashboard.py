import json
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.api.endpoints.dashboard import get_metrics_trend
from app.core.database import SessionLocal

def test_dashboard_trend():
    print("--- Testing Dashboard Trend API ---")
    db = SessionLocal()
    try:
        # Simulate local call
        response = get_metrics_trend(client_id=None, db=db)
        print("Response Summary:")
        print(f"  - Number of trend data points: {len(response['trend'])}")
        if response['trend']:
            print(f"  - First data point: {response['trend'][0]}")
            print(f"  - Last data point: {response['trend'][-1]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
    print("\n--- Dashboard Trend Test Completed ---")

if __name__ == "__main__":
    test_dashboard_trend()
