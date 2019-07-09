OpenIDConnect Auth for Sentry
=============================

An SSO provider for Sentry which enables `OpenID Connect <http://openid.net/connect/>`_ Apps authentication.

This is a fork of `sentry-auth-google <https://github.com/getsentry/sentry-auth-google/>`_.

Why fork, instead of adapting sentry-auth-google to work with every OpenID Connect provider?
--------------------------------------------------------------------------------------------
The maintainer has different ideas with sentry-auth-google. See:

* https://github.com/getsentry/sentry-auth-google/pull/29
* https://github.com/getsentry/sentry/issues/5650

Install
-------

::

    $ pip install sentry-auth-oidc

Example Setup for Google
------------------------

Start by `creating a project in the Google Developers Console <https://console.developers.google.com>`_.

In the **Authorized redirect URIs** add the SSO endpoint for your installation::

    https://sentry.example.com/auth/sso/

Naturally other providers, that are supporting OpenID-Connect can also be used (like GitLab).

Finally, obtain the API keys and the well-known account URL and plug them into your ``sentry.conf.py``:

.. code-block:: python

    OIDC_CLIENT_ID = ""

    OIDC_CLIENT_SECRET = ""

    OIDC_SCOPE = "openid email"

    OIDC_DOMAIN = "https://accounts.google.com"  # e.g. for Google

The ``OIDC_DOMAIN`` defines where the OIDC configuration is going to be pulled from.
Basically it specifies the OIDC server and adds the path ``.well-known/openid-configuration`` to it.
That's where different endpoint paths can be found.

Detailed information can be found in the `ProviderConfig <https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig>`_ specification.

You can also define ``OIDC_ISSUER`` to change the default provider name in the UI, even when the ``OIDC_DOMAIN`` is set.

If your provider doesn't support the ``OIDC_DOMAIN``, then you have to set these
required endpoints by yourself (autorization_endpoint, token_endpoint, userinfo_endpoint, issuer).

.. code-block:: python

    OIDC_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"  # e.g. for Google

    OIDC_TOKEN_ENDPOINT = "https://www.googleapis.com/oauth2/v4/token"  # e.g. for Google

    OIDC_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo" # e.g. for Google

    OIDC_ISSUER = "Google"
