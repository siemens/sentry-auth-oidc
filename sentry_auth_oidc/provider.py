from __future__ import absolute_import, print_function

import requests

from sentry.auth.providers.oauth2 import (
    OAuth2Callback, OAuth2Provider, OAuth2Login
)
from .constants import (
    AUTHORIZATION_ENDPOINT,
    USERINFO_ENDPOINT,
    ISSUER, TOKEN_ENDPOINT,
    CLIENT_SECRET,
    CLIENT_ID,
    SCOPE, DATA_VERSION
)
from .views import FetchUser, OIDCConfigureView
import logging
logger = logging.getLogger('sentry.auth.oidc')


class OIDCLogin(OAuth2Login):
    authorize_url = AUTHORIZATION_ENDPOINT
    client_id = CLIENT_ID
    scope = SCOPE

    def __init__(self, domains=None):
        self.domains = domains
        super(OIDCLogin, self).__init__()

    def get_authorize_params(self, state, redirect_uri):
        params = super(OIDCLogin, self).get_authorize_params(
            state, redirect_uri
        )
        # TODO(dcramer): ideally we could look at the current resulting state
        # when an existing auth happens, and if they're missing a refresh_token
        # we should re-prompt them a second time with ``approval_prompt=force``
        params['approval_prompt'] = 'force'
        params['access_type'] = 'offline'
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
        super(OIDCProvider, self).__init__(**config)

    def get_configure_view(self):
        return OIDCConfigureView.as_view()

    def get_auth_pipeline(self):
        return [
            OIDCLogin(domains=self.domains),
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
            'domains': [state['domain']],
            'version': DATA_VERSION,
        }

    def get_user_info(self, bearer_token):
        endpoint = USERINFO_ENDPOINT
        bearer_auth = 'Bearer ' + bearer_token
        return requests.get(endpoint + "?schema=openid",
                            headers={'Authorization': bearer_auth},
                            timeout=2.0).json()

    def build_identity(self, state):
        data = state['data']
        bearer_token = data['access_token']
        user_info = self.get_user_info(bearer_token)
        if not user_info.get('email'):
            logger.error('Missing email in user endpoint: %s' % data)

        user_data = state['user']
        return {
            'id': user_data.get('sub'),
            'email': user_info.get('email'),
            'email_verified': user_info.get('email_verified'),
            'nickname': user_info.get('nickname'),
            'name': user_info.get('name'),
            'data': self.get_oauth_data(data),
        }
