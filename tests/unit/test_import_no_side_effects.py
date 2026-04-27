"""
Test to verify that importing application modules does NOT initialize infrastructure.

This test ensures that unit tests can safely import DTOs, use cases, and entities
without requiring a database connection or environment variables.

Key assertion:
  - Importing app.modules.*.application.* should NOT trigger engine creation
  - The _engine variable in app.shared.infra.db should remain None after imports
"""

import sys
from unittest import mock


def test_importing_dtos_does_not_initialize_engine():
    """
    Verify that importing DTOs doesn't trigger engine initialization.
    
    This is the most common use case: unit tests import DTOs without needing DB.
    """
    # Clear any cached imports to simulate fresh test collection
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith("app")]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    # Reset engine cache before import
    import importlib
    import app.shared.infra.db
    importlib.reload(app.shared.infra.db)
    
    # Now import DTOs - should NOT create engine
    from app.modules.iam.application.dtos.usuario import (
        AtualizarUsuario,
        CriarUsuarioRequest,
        UsuarioResponse,
    )
    
    # Verify engine was NOT created
    assert app.shared.infra.db._engine is None, \
        "Engine should not be initialized when importing DTOs"
    
    # Verify the DTOs are usable
    assert AtualizarUsuario is not None
    assert CriarUsuarioRequest is not None
    assert UsuarioResponse is not None


def test_importing_use_cases_does_not_initialize_engine():
    """
    Verify that importing use cases doesn't trigger engine initialization.
    """
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith("app")]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    import importlib
    import app.shared.infra.db
    importlib.reload(app.shared.infra.db)
    
    # Import use cases
    from app.modules.iam.application.use_cases.criar_usuario import CriarUsuarioUseCase
    
    # Verify engine was NOT created
    assert app.shared.infra.db._engine is None, \
        "Engine should not be initialized when importing use cases"
    
    # Verify the use case is importable
    assert CriarUsuarioUseCase is not None


def test_importing_domain_entities_does_not_initialize_engine():
    """
    Verify that importing domain entities doesn't trigger engine initialization.
    """
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith("app")]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    import importlib
    import app.shared.infra.db
    importlib.reload(app.shared.infra.db)
    
    # Import domain entities
    from app.modules.iam.domain.entities.usuario import Usuario
    
    # Verify engine was NOT created
    assert app.shared.infra.db._engine is None, \
        "Engine should not be initialized when importing domain entities"
    
    # Verify the entity is importable
    assert Usuario is not None


def test_config_does_not_require_db_url_for_import():
    """
    Verify that importing app.config doesn't fail even with empty DB_URL.
    
    DB_URL validation is deferred to runtime (when server starts).
    """
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith("app")]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    # This should NOT raise ValidationError, even though DB_URL is empty
    from app.config import get_settings
    
    settings = get_settings()
    assert settings.DB_URL == ""  # Default empty value
    # No exception should be raised


def test_settings_validates_on_server_start():
    """
    Verify that DB_URL validation happens explicitly, not during Settings creation.
    """
    from app.config import get_settings
    
    settings = get_settings()
    settings.DB_URL = ""  # Reset to empty
    
    # Should raise when we explicitly validate for server start
    try:
        settings.validate_for_server_start()
        assert False, "Should have raised ValueError for empty DB_URL"
    except ValueError as e:
        assert "Database URL is required" in str(e)


if __name__ == "__main__":
    test_importing_dtos_does_not_initialize_engine()
    test_importing_use_cases_does_not_initialize_engine()
    test_importing_domain_entities_does_not_initialize_engine()
    test_config_does_not_require_db_url_for_import()
    test_settings_validates_on_server_start()
    print("✅ All side-effect tests passed!")
