from __future__ import absolute_import, print_function

from django.conf import settings
import requests

AUTHORIZATION_ENDPOINT = getattr(settings, 'AUTHORIZATION_ENDPOINT', None)
TOKEN_ENDPOINT = getattr(settings, 'TOKEN_ENDPOINT', None)
CLIENT_ID = getattr(settings, 'CLIENT_ID', None)
CLIENT_SECRET = getattr(settings, 'CLIENT_SECRET', None)
USERINFO_ENDPOINT = getattr(settings, 'USERINFO_ENDPOINT', None)
SCOPE = getattr(settings, 'SCOPE', 'openid email')
ISSUER = getattr(settings, 'ISSUER', None)

WELL_KNOWN_SCHEME = "/.well-known/openid-configuration"
ERR_INVALID_RESPONSE = 'Unable to fetch user information from provider.  Please check the log.'
DATA_VERSION = '1'

WELL_KNOWN_URL = getattr(settings, 'WELL_KNOWN_URL', None)
if WELL_KNOWN_URL:
    WELL_KNOWN_URL = WELL_KNOWN_URL.strip("/") + WELL_KNOWN_SCHEME
    well_known_values = requests.get(WELL_KNOWN_URL, timeout=2.0).json()
    if well_known_values:
        USERINFO_ENDPOINT = well_known_values['userinfo_endpoint']
        AUTHORIZATION_ENDPOINT = well_known_values['authorization_endpoint']
        TOKEN_ENDPOINT = well_known_values['token_endpoint']
        ISSUER = well_known_values['issuer']
