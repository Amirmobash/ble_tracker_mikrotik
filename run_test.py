# test_imports.py
import sys
print("Python path:")
for path in sys.path:
    print("  ", path)

print("\nTrying imports...")

try:
    from app.core.config import settings
    print("✓ app.core.config imported")
except Exception as e:
    print(f"✗ app.core.config error: {e}")

try:
    from app.core.logging_config import configure_logging
    print("✓ app.core.logging_config imported")
except Exception as e:
    print(f"✗ app.core.logging_config error: {e}")

try:
    from app.api.router_ingest import router as ingest_router
    print("✓ app.api.router_ingest imported")
except Exception as e:
    print(f"✗ app.api.router_ingest error: {e}")