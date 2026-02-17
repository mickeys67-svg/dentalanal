import sys
import os
import importlib
import traceback

# Add backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

modules_to_check = [
    "app.main",
    "app.core.config",
    "app.api.endpoints.naver_auth",
    "app.external_apis.naver_search",
    "app.scrapers.naver_view",
    "app.scrapers.base",
]

print("Starting Backend Integrity Check...")
failed = False

for module_name in modules_to_check:
    try:
        print(f"Checking {module_name}...", end=" ")
        importlib.import_module(module_name)
        print("OK")
    except Exception as e:
        print("FAILED")
        print(f"Error importing {module_name}:")
        traceback.print_exc()
        failed = True

if failed:
    print("\nIntegrity Check FAILED")
    sys.exit(1)
else:
    print("\nIntegrity Check PASSED")
    sys.exit(0)
