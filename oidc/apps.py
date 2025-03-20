from inspect import signature

from django.apps import AppConfig


class Config(AppConfig):
    name = "oidc"

    def ready(self):
        from sentry import auth

        from .provider import OIDCProvider

        # In Sentry 25.3.0, the signature of `ProviderManager.register()` changed:
        # Instead of providing the key as a parameter, it is now expected to be a
        # property of the provider class.
        if len(signature(auth.register).parameters) == 1:
            auth.register(OIDCProvider)
        else:
            auth.register("oidc", OIDCProvider)
