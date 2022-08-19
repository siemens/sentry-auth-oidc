import time

import requests
from sentry.auth.provider import MigratingIdentityId
from sentry.auth.providers.oauth2 import OAuth2Callback, OAuth2Login, OAuth2Provider

from .constants import (
    AUTHORIZATION_ENDPOINT,
    CLIENT_ID,
    CLIENT_SECRET,
    DATA_VERSION,
    ISSUER,
    SCOPE,
    TOKEN_ENDPOINT,
    USERINFO_ENDPOINT,
)
from .views import FetchUser, OIDCConfigureView


class OIDCLogin(OAuth2Login):
    authorize_url = AUTHORIZATION_ENDPOINT
    client_id = CLIENT_ID
    scope = SCOPE

    def __init__(self, client_id, domains=None):
        self.domains = domains
        super().__init__(client_id=client_id)

    def get_authorize_params(self, state, redirect_uri):
        params = super().get_authorize_params(state, redirect_uri)
        # TODO(dcramer): ideally we could look at the current resulting state
        # when an existing auth happens, and if they're missing a refresh_token
        # we should re-prompt them a second time with ``approval_prompt=force``
        params["approval_prompt"] = "force"
        params["access_type"] = "offline"
        return params


class OIDCProvider(OAuth2Provider):
    name = ISSUER
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    def __init__(self, domain=None, domains=None, version=None, **config):
        if domain:
            if domains:
                domains.append(domain)
            else:
                domains = [domain]
        self.domains = domains
        # if a domain is not configured this is part of the setup pipeline
        # this is a bit complex in Sentry's SSO implementation as we don't
        # provide a great way to get initial state for new setup pipelines
        # vs missing state in case of migrations.
        if domains is None:
            version = DATA_VERSION
        else:
            version = None
        self.version = version
        super().__init__(**config)

    def get_configure_view(self):
        return OIDCConfigureView.as_view()

    def get_auth_pipeline(self):
        return [
            OIDCLogin(self.client_id, domains=self.domains),
            OAuth2Callback(
                access_token_url=TOKEN_ENDPOINT,
                client_id=self.client_id,
                client_secret=self.client_secret,
            ),
            FetchUser(
                domains=self.domains,
                version=self.version,
            ),
        ]

    def get_refresh_token_url(self):
        return TOKEN_ENDPOINT

    def build_config(self, state):
        return {
            "domains": [state["domain"]],
            "version": DATA_VERSION,
        }

    def get_user_info(self, bearer_token):
        endpoint = USERINFO_ENDPOINT
        bearer_auth = "Bearer " + bearer_token
        retry_codes = [429, 500, 502, 503, 504]
        for retry in range(10):
            if 10 < retry:
                return {}
            r = requests.get(
                endpoint + "?schema=openid",
                headers={"Authorization": bearer_auth},
                timeout=2.0,
            )
            if r.status_code in retry_codes:
                wait_time = 2**retry * 0.1
                time.sleep(wait_time)
                continue
            return r.json()

    def build_identity(self, state):
        data = state["data"]
        user_data = state["user"]

        bearer_token = data["access_token"]
        user_info = self.get_user_info(bearer_token)

        # XXX(epurkhiser): We initially were using the email as the id key.
        # This caused account dupes on domain changes. Migrate to the
        # account-unique sub key.
        user_id = MigratingIdentityId(id=user_data["sub"], legacy_id=user_data["email"])

        return {
            "id": user_id,
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "data": self.get_oauth_data(data),
            "email_verified": user_info.get("email_verified"),
        }
