# app/__init__.py
# This module is intentionally minimal to avoid side effects during import.
# All bootstrap logic has been moved to app.main to ensure:
# - Unit tests can import application/domain modules without initializing infrastructure
# - Database engine is not created until explicitly needed
# - Settings validation only happens when the server actually starts
#
# Use:
#   python -m app  # starts server
# Or:
#   from app.main import create_app, get_settings  # in production code
#   from app.modules.iam.application.dtos import ...  # in tests (no side effects)
