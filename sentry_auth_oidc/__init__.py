from __future__ import absolute_import

from sentry.auth import register

from .provider import OIDCProvider

register('oidc', OIDCProvider)
