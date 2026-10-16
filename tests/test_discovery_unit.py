import sys

import pytest
import requests
from django.test import override_settings

from tests.test_provider_unit import stubbed_provider_module

WELL_KNOWN = {
    "issuer": "https://idp.example.com",
    "authorization_endpoint": "https://idp.example.com/authorize",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


@pytest.fixture
def requests_get(monkeypatch):
    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        if isinstance(calls_behaviour[0], Exception):
            raise calls_behaviour[0]
        return FakeResponse(calls_behaviour[0])

    calls_behaviour = [WELL_KNOWN]
    monkeypatch.setattr(requests, "get", fake_get)
    return calls, calls_behaviour


@pytest.fixture
def provider_with_domain(requests_get):
    with (
        override_settings(OIDC_DOMAIN="https://idp.example.com/"),
        stubbed_provider_module() as provider_module,
    ):
        yield provider_module.OIDCProvider, sys.modules["oidc.constants"]


def test_import_does_not_fetch_discovery_document(provider_with_domain, requests_get):
    calls, _ = requests_get
    _, constants = provider_with_domain

    assert calls == []
    assert constants.WELL_KNOWN_URL == "https://idp.example.com/.well-known/openid-configuration"


def test_discovery_document_is_fetched_on_first_use_and_cached(provider_with_domain, requests_get):
    calls, _ = requests_get
    provider_cls, constants = provider_with_domain

    provider = provider_cls(domains=["example.com"])
    login, callback, _ = provider.get_auth_pipeline()

    assert login.authorize_url == WELL_KNOWN["authorization_endpoint"]
    assert callback.kwargs["access_token_url"] == WELL_KNOWN["token_endpoint"]
    assert provider.get_refresh_token_url() == WELL_KNOWN["token_endpoint"]
    assert constants.get_userinfo_endpoint() == WELL_KNOWN["userinfo_endpoint"]
    assert constants.get_issuer() == WELL_KNOWN["issuer"]
    assert constants.get_provider_name() == WELL_KNOWN["issuer"]
    assert calls == [constants.WELL_KNOWN_URL]


def test_failed_fetch_falls_back_to_static_settings_and_does_not_raise(
    provider_with_domain, requests_get
):
    calls, behaviour = requests_get
    behaviour[0] = requests.exceptions.ReadTimeout("simulated timeout")
    provider_cls, constants = provider_with_domain

    provider = provider_cls(domains=["example.com"])
    login, callback, _ = provider.get_auth_pipeline()

    # Static endpoints come from settings.configure() in tests/test_provider_unit.py.
    assert login.authorize_url == "https://example.com/auth"
    assert callback.kwargs["access_token_url"] == "https://example.com/token"
    assert constants.get_userinfo_endpoint() == "https://example.com/userinfo"
    assert constants.get_provider_name() == "OIDC"
    # The failed attempt is not retried before OIDC_WELL_KNOWN_RETRY_AFTER has elapsed.
    assert len(calls) == 1

    constants._well_known_last_failure = 0.0
    behaviour[0] = WELL_KNOWN
    assert provider.get_refresh_token_url() == WELL_KNOWN["token_endpoint"]
    assert len(calls) == 2


def test_configured_issuer_takes_precedence_over_discovery(requests_get):
    with (
        override_settings(OIDC_DOMAIN="https://idp.example.com", OIDC_ISSUER="Custom Issuer"),
        stubbed_provider_module() as provider_module,
    ):
        constants = sys.modules["oidc.constants"]
        assert provider_module.OIDCProvider.name == "Custom Issuer"
        assert constants.get_issuer() == "Custom Issuer"
        assert constants.get_provider_name() == "Custom Issuer"


def test_without_domain_static_settings_are_used(requests_get):
    calls, _ = requests_get
    with stubbed_provider_module() as provider_module:
        constants = sys.modules["oidc.constants"]
        provider = provider_module.OIDCProvider(domains=["example.com"])
        login, _, _ = provider.get_auth_pipeline()

        assert constants.WELL_KNOWN_URL is None
        assert login.authorize_url == "https://example.com/auth"
        assert calls == []
