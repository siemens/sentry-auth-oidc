from django.apps import AppConfig


class Config(AppConfig):
    name = "oidc"
    _oidc_middleware = 'oidc.middleware.PatchLoginPage'

    def ready(self):
        from sentry import auth
        from django.conf import settings
        from .provider import OIDCProvider

        auth.register("oidc", OIDCProvider)

        if self._oidc_middleware not in settings.MIDDLEWARE_CLASSES:
            settings.MIDDLEWARE_CLASSES += self._oidc_middleware
