from __future__ import absolute_import
from django.apps import AppConfig


class Config(AppConfig):
    name = "oidc"

    def ready(self):
        from sentry import auth
        from .provider import OIDCProvider

        auth.register('oidc', OIDCProvider)
