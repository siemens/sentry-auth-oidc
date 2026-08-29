import base64
import hashlib
import json
import sys
import types
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import import_module

import pytest
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


REDIRECT_URI = "https://sentry.example.com/auth/sso/"


class MigratingIdentityId:
    def __init__(self, id, legacy_id):
        self.id = id
        self.legacy_id = legacy_id


class OAuth2Login:
    def __init__(self, client_id):
        self.client_id = client_id

    def get_authorize_params(self, state, redirect_uri):
        return {}

    def dispatch(self, request, **kwargs):
        # The real one redirects to the authorize URL it builds from these.
        return self.get_authorize_params(state="state", redirect_uri=REDIRECT_URI)


class OAuth2Callback:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_token_params(self, code, redirect_uri):
        return {"code": code, "redirect_uri": redirect_uri}

    def exchange_token(self, request, pipeline, code):
        # The real one posts these to the token endpoint.
        return self.get_token_params(code=code, redirect_uri=REDIRECT_URI)


class Pipeline(dict):
    def bind_state(self, key, value):
        self[key] = value

    def fetch_state(self, key=None):
        return self.get(key)


class Request:
    def __init__(self, **query):
        self.GET = query


class OAuth2Provider:
    def __init__(self, **config):
        self.config = config

    def get_oauth_data(self, payload):
        return payload


SENTRY_STUB_MODULES = [
    "sentry",
    "sentry.auth",
    "sentry.auth.provider",
    "sentry.auth.view",
    "sentry.auth.providers.oauth2",
    "sentry.auth.services.auth.model",
    "sentry.organizations.services.organization.model",
    "sentry.plugins.base.response",
    "sentry.utils",
    "sentry.utils.signing",
]
OIDC_MODULES = ["oidc.constants", "oidc.views", "oidc.provider"]
MISSING = object()


def module(name, **attrs):
    value = types.ModuleType(name)
    for key, attr in attrs.items():
        setattr(value, key, attr)
    sys.modules[name] = value
    return value


@contextmanager
def stubbed_provider_module() -> Iterator[types.ModuleType]:
    module_names = [*SENTRY_STUB_MODULES, *OIDC_MODULES]
    previous_modules = {name: sys.modules.get(name, MISSING) for name in module_names}

    try:
        for name in OIDC_MODULES:
            sys.modules.pop(name, None)

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

        yield import_module("oidc.provider")
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module


@pytest.fixture
def oidc_provider():
    with stubbed_provider_module() as provider_module:
        yield provider_module.OIDCProvider


@pytest.fixture
def oidc_module():
    with stubbed_provider_module() as provider_module:
        yield provider_module


def test_build_identity_uses_default_userinfo_name_claim(oidc_provider):
    provider = oidc_provider(domains=["example.com"])
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


def test_build_identity_uses_configured_userinfo_name_claim(monkeypatch, oidc_provider):
    provider = oidc_provider(domains=["example.com"])
    provider_module = sys.modules["oidc.provider"]
    monkeypatch.setattr(provider_module, "USERINFO_NAME_CLAIM", "preferred_username", raising=False)
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


def test_login_challenges_the_verifier_it_bound(oidc_module):
    login = oidc_module.OIDCLogin(client_id="client-id")
    pipeline = Pipeline()

    params = login.dispatch(Request(), pipeline=pipeline)

    verifier = pipeline["code_verifier"]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    assert 43 <= len(verifier) <= 128
    assert params["code_challenge"] == base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    assert params["code_challenge_method"] == "S256"


def test_login_keeps_the_verifier_when_the_callback_re_enters_the_step(oidc_module):
    login = oidc_module.OIDCLogin(client_id="client-id")
    pipeline = Pipeline()
    login.dispatch(Request(), pipeline=pipeline)
    verifier = pipeline["code_verifier"]

    login.dispatch(Request(code="a-code"), pipeline=pipeline)

    assert pipeline["code_verifier"] == verifier


def test_login_sends_no_challenge_when_pkce_is_disabled(monkeypatch, oidc_module):
    monkeypatch.setattr(oidc_module, "USE_PKCE", False)
    login = oidc_module.OIDCLogin(client_id="client-id")
    pipeline = Pipeline()

    params = login.dispatch(Request(), pipeline=pipeline)

    assert "code_challenge" not in params
    assert "code_verifier" not in pipeline


def test_callback_sends_the_verifier_the_login_bound(oidc_module):
    callback = oidc_module.OIDCCallback()

    params = callback.exchange_token(Request(), Pipeline(code_verifier="the-verifier"), "a-code")

    assert params["code_verifier"] == "the-verifier"


def test_callback_sends_no_verifier_when_none_was_bound(oidc_module):
    callback = oidc_module.OIDCCallback()

    params = callback.exchange_token(Request(), Pipeline(), "a-code")

    assert "code_verifier" not in params


def test_auth_pipeline_uses_the_callback_that_sends_the_verifier(oidc_module):
    _, callback, _ = oidc_module.OIDCProvider(domains=["example.com"]).get_auth_pipeline()

    assert isinstance(callback, oidc_module.OIDCCallback)
