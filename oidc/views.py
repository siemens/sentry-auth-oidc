import logging
import requests

from sentry.auth.view import AuthView, ConfigureView
from sentry.utils import json
from sentry.utils.signing import urlsafe_b64decode
from .constants import (
    USERINFO_ENDPOINT,
)

from .constants import ERR_INVALID_RESPONSE, ISSUER

logger = logging.getLogger("sentry.auth.oidc")


class FetchUser(AuthView):
    def __init__(self, domains, version, *args, **kwargs):
        self.domains = domains
        self.version = version
        super().__init__(*args, **kwargs)

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

    def dispatch(self, request, helper):
        data = helper.fetch_state("data")

        try:
            access_token = data["access_token"]
        except KeyError:
            logger.error("Missing access_token in OAuth response: %s" % data)
            return helper.error(ERR_INVALID_RESPONSE)

        payload = self.get_user_info(access_token)

        # support legacy style domains with pure domain regexp
        if self.version is None:
            domain = extract_domain(payload["email"])
        else:
            domain = payload.get("hd")

        helper.bind_state("domain", domain)
        helper.bind_state("user", payload)

        return helper.next_step()


class OIDCConfigureView(ConfigureView):
    def dispatch(self, request, organization, auth_provider):
        config = auth_provider.config
        if config.get("domain"):
            domains = [config["domain"]]
        else:
            domains = config.get("domains")
        return self.render(
            "oidc/configure.html",
            {"provider_name": ISSUER or "", "domains": domains or []},
        )


def extract_domain(email):
    return email.rsplit("@", 1)[-1]
