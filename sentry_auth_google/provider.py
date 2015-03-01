from __future__ import absolute_import, print_function

from django.conf import settings

from sentry.auth.providers.oauth2 import (
    OAuth2Callback, OAuth2Provider, OAuth2Login
)

from .constants import (
    AUTHORIZE_URL, ACCESS_TOKEN_URL, CLIENT_ID, CLIENT_SECRET, SCOPE,
    USER_DETAILS_ENDPOINT
)
from .views import FetchUser, GoogleConfigureView


class GoogleOAuth2Provider(OAuth2Provider):
    name = 'Google'

    def __init__(self, domain=None, **config):
        self.domain = domain
        super(GoogleOAuth2Provider, self).__init__(**config)

    def get_configure_view(self):
        return GoogleConfigureView.as_view()

    def get_auth_pipeline(self):
        if self.domain:
            authorize_url = '{}?hd={}'.format(AUTHORIZE_URL, self.domain)
        else:
            authorize_url = AUTHORIZE_URL
        return [
            OAuth2Login(
                authorize_url=authorize_url,
                scope=SCOPE,
                client_id=CLIENT_ID,
            ),
            OAuth2Callback(
                access_token_url=ACCESS_TOKEN_URL,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
            ),
            FetchUser(domain=self.domain),
        ]

    def build_config(self, state):
        # TODO(dcramer): we actually want to enforce a domain here. Should that
        # be a view which does that, or should we allow this step to raise
        # validation errors?
        return {
            'domain': state['user']['domain'],
        }

    def build_identity(self, state):
        # data.user => {
        #   "displayName": "David Cramer",
        #   "emails": [{"value": "david@getsentry.com", "type": "account"}],
        #   "domain": "getsentry.com",
        #   "verified": false
        # }
        user_data = state['user']
        return {
            'id': user_data['id'],
            # TODO: is there a "correct" email?
            'email': user_data['emails'][0]['value'],
            'name': user_data['displayName'],
            'data': {
                'access_token': state['data']['access_token'],
            },
        }

    def identity_is_valid(self, auth_identity):
        access_token = auth_identity.data['access_token']

        req = safe_urlopen('{0}?{1}'.format(
            USER_DETAILS_ENDPOINT,
            urlencode({
                'access_token': access_token,
            }),
        ))

        if req.status_code == 401:
            return False
        return True