# Copilot Instructions for sentry-auth-oidc

## Project Overview

This is an OpenID Connect (OIDC) authentication provider plugin for Sentry. It's based on `sentry-auth-google` and enables SSO authentication using any OIDC-compliant provider (Google, GitLab, etc.).

## Key Architecture

- **Language**: Python 3.11+
- **Framework**: Django-based Sentry plugin
- **Package Manager**: Poetry
- **Plugin Type**: Sentry auth provider using OAuth2 flow

## Important Files and Structure

- `oidc/provider.py`: Main provider implementation (`OIDCProvider` and `OIDCLogin`)
- `oidc/views.py`: Authentication views (`FetchUser` and configure view)
- `oidc/constants.py`: Configuration constants loaded from Django settings
- `oidc/apps.py`: Django app configuration with Sentry registration
- `tests/test_provider.py`: Provider tests using Sentry's test framework

## Development Setup

1. **Install dependencies**:
   ```bash
   poetry install --with test
   make deps  # Fetches Sentry dev dependencies via git submodule
   ```

2. **Dependencies**: This project has a git submodule dependency on Sentry itself (`deps/sentry`) to access development dependencies and test fixtures.

## Code Style and Linting

- **Formatter**: Black (with `deps` directory excluded)
- **Import Sorter**: isort (using Black profile)
- **Linter**: flake8
- **Line length**: Follow Black's defaults

Run formatting/linting:
```bash
poetry run black .
poetry run isort .
poetry run flake8
```

## Testing

- **Framework**: pytest
- **Test Location**: `tests/` directory
- **Sentry Test Utils**: Uses `sentry.testutils.cases.TestCase` and fixtures from Sentry
- **Required Decorators**: Use `@control_silo_test` for auth provider tests

Run tests:
```bash
poetry run pytest
```

Tests require PostgreSQL, Memcached, and Redis (see `.github/workflows/test.yml` for service configuration).

## Key Patterns and Conventions

### OIDC Configuration
The plugin supports two configuration modes:
1. **Auto-discovery** via `OIDC_DOMAIN` - fetches endpoints from `/.well-known/openid-configuration`
2. **Manual configuration** - explicitly set `OIDC_AUTHORIZATION_ENDPOINT`, `OIDC_TOKEN_ENDPOINT`, etc.

### Sentry Version Compatibility
The code includes compatibility checks for different Sentry versions:
- `apps.py`: Handles signature changes in `auth.register()` (Sentry 25.3.0+)
- `views.py`: Handles `helper` renamed to `pipeline` parameter (Sentry 25.6.0+)

Always check method signatures before making changes to maintain backward compatibility.

### Identity Migration
- Uses `MigratingIdentityId` to handle legacy email-based IDs migrating to `sub`-based IDs
- This prevents account duplication on domain changes

### Data Versioning
- `DATA_VERSION` constant tracks configuration schema versions
- Increment when making breaking changes to provider config structure

## Common Tasks

### Adding New Configuration Options
1. Add constant to `oidc/constants.py` using `getattr(settings, "OIDC_...", default)`
2. Update provider initialization in `provider.py`
3. Document in `README.rst`
4. Add test coverage in `tests/test_provider.py`

### Modifying Authentication Flow
The auth pipeline has three steps (in `OIDCProvider.get_auth_pipeline()`):
1. `OIDCLogin`: Initiates OAuth2 authorization
2. `OAuth2Callback`: Exchanges code for tokens
3. `FetchUser`: Validates and extracts user info from ID token

### Error Handling
- Use logger (`sentry.auth.oidc`) for authentication errors
- Return `pipeline.error(ERR_INVALID_RESPONSE)` for invalid OIDC responses
- Include retry logic for transient HTTP errors (see `get_user_info()`)

## Important Constraints

- **Minimal changes**: This is a stable plugin - avoid unnecessary refactoring
- **Sentry dependency**: Changes must be compatible with Sentry's internal APIs
- **No breaking changes**: Maintain backward compatibility with existing deployments
- **Security**: Never log sensitive data (tokens, secrets, PII)

## Release Process

- Publishing is automated via GitHub Actions on tag push
- Package is published to PyPI
- Version is managed in `pyproject.toml`
