import json
import sys
import types

from django.conf import settings

if not settings.configured:
    settings.configure(
        OIDC_AUTHORIZATION_ENDPOINT="https://example.com/auth",
        OIDC_CLIENT_ID="client-id",
        OIDC_CLIENT_SECRET="client-secret",
        OIDC_TOKEN_ENDPOINT="https://example.com/token",
        OIDC_USERINFO_ENDPOINT="https://example.com/userinfo",
        SENTRY_METRICS_SKIP_ALL_INTERNAL=True,
        SENTRY_METRICS_SKIP_INTERNAL_PREFIXES=[],
        SENTRY_METRICS_BACKEND="sentry.metrics.dummy.DummyMetricsBackend",
        SENTRY_METRICS_OPTIONS={},
        SENTRY_METRICS_PREFIX="sentry",
        SENTRY_METRICS_SAMPLE_RATE=1.0,
    )


class MigratingIdentityId:
    def __init__(self, id, legacy_id):
        self.id = id
        self.legacy_id = legacy_id


class OAuth2Login:
    def __init__(self, client_id):
        self.client_id = client_id

    def get_authorize_params(self, state, redirect_uri):
        return {}


class OAuth2Callback:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class OAuth2Provider:
    def __init__(self, **config):
        self.config = config

    def get_oauth_data(self, payload):
        return payload


def module(name, **attrs):
    value = types.ModuleType(name)
    for key, attr in attrs.items():
        setattr(value, key, attr)
    sys.modules[name] = value
    return value


module("sentry", auth=types.SimpleNamespace())
module("sentry.auth")
module("sentry.auth.provider", MigratingIdentityId=MigratingIdentityId)
module("sentry.auth.view", AuthView=object)
module(
    "sentry.auth.providers.oauth2",
    OAuth2Callback=OAuth2Callback,
    OAuth2Login=OAuth2Login,
    OAuth2Provider=OAuth2Provider,
)
module("sentry.auth.services.auth.model", RpcAuthProvider=object)
module("sentry.organizations.services.organization.model", RpcOrganization=object)
module("sentry.plugins.base.response", DeferredResponse=object)
module("sentry.utils", json=json)
module("sentry.utils.signing", urlsafe_b64decode=lambda value: value)

from oidc.provider import OIDCProvider


def test_build_identity_uses_default_userinfo_name_claim():
    provider = OIDCProvider(domains=["example.com"])
    provider.get_user_info = lambda token: {
        "email": "jsmith@example.com",
        "name": "John Smith",
        "email_verified": True,
    }

    result = provider.build_identity(
        {
            "data": {"access_token": "access_token", "token_type": "Bearer"},
            "user": {
                "sub": "10769150350006150715113082367",
                "email": "jsmith@example.com",
            },
        }
    )

    assert result["name"] == "John Smith"


def test_build_identity_uses_configured_userinfo_name_claim(monkeypatch):
    provider = OIDCProvider(domains=["example.com"])
    monkeypatch.setattr("oidc.provider.USERINFO_NAME_CLAIM", "preferred_username", raising=False)
    monkeypatch.setattr(
        provider,
        "get_user_info",
        lambda token: {
            "email": "jsmith@example.com",
            "preferred_username": "jsmith",
            "email_verified": True,
        },
    )

    result = provider.build_identity(
        {
            "data": {"access_token": "access_token", "token_type": "Bearer"},
            "user": {
                "sub": "10769150350006150715113082367",
                "email": "jsmith@example.com",
            },
        }
    )

    assert result["name"] == "jsmith"
