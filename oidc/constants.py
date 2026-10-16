from __future__ import annotations

import logging
import threading
import time

import requests
from django.conf import settings

logger = logging.getLogger("sentry.auth.oidc")

# Statically configured values. They are used as-is when OIDC_DOMAIN is not set
# and act as fallbacks while the discovery document cannot be fetched.
AUTHORIZATION_ENDPOINT = getattr(settings, "OIDC_AUTHORIZATION_ENDPOINT", None)
TOKEN_ENDPOINT = getattr(settings, "OIDC_TOKEN_ENDPOINT", None)
CLIENT_ID = getattr(settings, "OIDC_CLIENT_ID", None)
CLIENT_SECRET = getattr(settings, "OIDC_CLIENT_SECRET", None)
USERINFO_ENDPOINT = getattr(settings, "OIDC_USERINFO_ENDPOINT", None)
USERINFO_NAME_CLAIM = getattr(settings, "OIDC_USERINFO_NAME_CLAIM", "name")
SCOPE = getattr(settings, "OIDC_SCOPE", "openid email")
WELL_KNOWN_SCHEME = "/.well-known/openid-configuration"
ERR_INVALID_RESPONSE = "Unable to fetch user information from provider.  Please check the log."
ISSUER = getattr(settings, "OIDC_ISSUER", None)

DATA_VERSION = "1"

OIDC_DOMAIN = getattr(settings, "OIDC_DOMAIN", None)
WELL_KNOWN_URL = OIDC_DOMAIN.strip("/") + WELL_KNOWN_SCHEME if OIDC_DOMAIN else None
WELL_KNOWN_TIMEOUT = float(getattr(settings, "OIDC_WELL_KNOWN_TIMEOUT", 15.0))
# After a failed fetch, do not hit the provider again before this many seconds
# have passed so a slow or unavailable provider cannot stall every request.
WELL_KNOWN_RETRY_AFTER = float(getattr(settings, "OIDC_WELL_KNOWN_RETRY_AFTER", 30.0))

# Provider name for display in the Sentry UI. This is read as a class attribute
# at import time and therefore must never depend on network I/O.
PROVIDER_NAME = getattr(settings, "OIDC_PROVIDER_NAME", None) or ISSUER or "OIDC"

_well_known_lock = threading.Lock()
_well_known: dict | None = None
_well_known_last_failure: float = 0.0


def get_well_known() -> dict:
    """Return the provider's discovery document, fetching it on first use.

    The document is fetched lazily instead of at import time so that Sentry
    processes which never perform a login (e.g. consumers and workers) do not
    crash when the identity provider is slow or unavailable. The result is
    cached for the lifetime of the process; a failed fetch is logged and
    yields an empty dict so callers fall back to the statically configured
    endpoints.
    """
    global _well_known, _well_known_last_failure

    if _well_known is not None:
        return _well_known
    if not WELL_KNOWN_URL:
        return {}

    with _well_known_lock:
        if _well_known is not None:
            return _well_known
        if time.monotonic() - _well_known_last_failure < WELL_KNOWN_RETRY_AFTER:
            return {}
        try:
            response = requests.get(WELL_KNOWN_URL, timeout=WELL_KNOWN_TIMEOUT)
            response.raise_for_status()
            values = response.json()
            if not isinstance(values, dict) or not values:
                raise ValueError("discovery document is empty or not a JSON object")
        except Exception as exc:
            _well_known_last_failure = time.monotonic()
            logger.warning(
                "Unable to fetch OIDC discovery document from %s: %s", WELL_KNOWN_URL, exc
            )
            return {}
        _well_known = values
        return _well_known


def get_authorization_endpoint() -> str | None:
    return get_well_known().get("authorization_endpoint") or AUTHORIZATION_ENDPOINT


def get_token_endpoint() -> str | None:
    return get_well_known().get("token_endpoint") or TOKEN_ENDPOINT


def get_userinfo_endpoint() -> str | None:
    return get_well_known().get("userinfo_endpoint") or USERINFO_ENDPOINT


def get_issuer() -> str | None:
    # An explicitly configured OIDC_ISSUER takes precedence over discovery.
    return ISSUER or get_well_known().get("issuer")


def get_provider_name() -> str:
    """Display name for places that are rendered per request, e.g. the configure view."""
    return getattr(settings, "OIDC_PROVIDER_NAME", None) or get_issuer() or "OIDC"
