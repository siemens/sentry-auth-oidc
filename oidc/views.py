from __future__ import annotations

import logging

from django.http import HttpRequest
from rest_framework.response import Response

from sentry.auth.services.auth.model import RpcAuthProvider
from sentry.auth.view import AuthView
from sentry.utils import json
from sentry.organizations.services.organization.model import RpcOrganization
from sentry.plugins.base.response import DeferredResponse
from sentry.utils.signing import urlsafe_b64decode

from .constants import ERR_INVALID_RESPONSE, ISSUER

logger = logging.getLogger("sentry.auth.oidc")


class FetchUser(AuthView):
    def __init__(self, domains, version, *args, **kwargs):
        self.domains = domains
        self.version = version
        super().__init__(*args, **kwargs)

    def dispatch(self, request: HttpRequest, **kwargs) -> Response:  # type: ignore
        # Until Sentry 25.6.0, the second argument to this function was called `helper`
        # and was then renamed to `pipeline`.
        if "pipeline" in kwargs:
            pipeline = kwargs["pipeline"]
        elif "helper" in kwargs:
            pipeline = kwargs["helper"]
        else:
            raise TypeError(
                f"FetchUser.dispatch() is missing either the `pipeline` or the `helper` keyword argument."
            )

        data = pipeline.fetch_state("data")

        try:
            id_token = data["id_token"]
        except KeyError:
            logger.error("Missing id_token in OAuth response: %s" % data)
            return pipeline.error(ERR_INVALID_RESPONSE)

        try:
            _, payload, _ = map(urlsafe_b64decode, id_token.split(".", 2))
        except Exception as exc:
            logger.error("Unable to decode id_token: %s" % exc, exc_info=True)
            return pipeline.error(ERR_INVALID_RESPONSE)

        try:
            payload = json.loads(payload)
        except Exception as exc:
            logger.error("Unable to decode id_token payload: %s" % exc, exc_info=True)
            return pipeline.error(ERR_INVALID_RESPONSE)

        if not payload.get("email"):
            logger.error("Missing email in id_token payload: %s" % id_token)
            return pipeline.error(ERR_INVALID_RESPONSE)

        # support legacy style domains with pure domain regexp
        if self.version is None:
            domain = extract_domain(payload["email"])
        else:
            domain = payload.get("hd")

        pipeline.bind_state("domain", domain)
        pipeline.bind_state("user", payload)

        return pipeline.next_step()


def oidc_configure_view(
    request: HttpRequest, organization: RpcOrganization, auth_provider: RpcAuthProvider
) -> DeferredResponse:
    config = auth_provider.config
    if config.get("domain"):
        domains: list[str] | None
        domains = [config["domain"]]
    else:
        domains = config.get("domains")
    return DeferredResponse(
        "oidc/configure.html", {"provider_name": ISSUER or "", "domains": domains or []}
    )


def extract_domain(email):
    return email.rsplit("@", 1)[-1]
