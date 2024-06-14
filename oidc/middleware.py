from django.urls import reverse
from typing import Union
from bs4 import BeautifulSoup, Tag
from logging import debug, info, error
from sentry.models import Organization, AuthProvider
from .constants import ORGS_SLUG_REGEX


class PatchLoginPage:
    def __init__(self, *args, **kwargs):
        self._sentry_login_url_path = reverse('sentry-login')

    def process_response(
            self, request: 'django.http.HttpRequest',
            response: Union[
                'django.http.HttpResponse',
                'django.http.StreamingHttpResponse']):
        try:
            if (
                    request.method != 'GET'
                    or
                    request.path_info != self._sentry_login_url_path
                    or
                    request.user.is_authenticated
                    ):
                return
            #
            _soup = BeautifulSoup(response._container[0], 'lxml')
            _tab_content = _soup.find("div", {"class": "tab-content"})
            if not _tab_content:
                return
            _auth_container = _tab_content.find(
                'div', {"class": "auth-container"})
            if not _auth_container:
                return
            #
            _auth_provider_column = _auth_container.find(
                'div', {"class": "auth-provider-column"})
            if not _auth_provider_column:
                _auth_provider_column = Tag(
                    name='div', attrs={"class": "auth-provider-column"})
                _auth_container.append(_auth_provider_column)
            #
            _orgs = Organization.objects.filter(
                slug__regex=ORGS_SLUG_REGEX,
                id__in=(AuthProvider.objects.filter(provider='oidc')
                                            .values('organization_id')))
            for org in _orgs:
                _p = self._login_link_for(org)
                _auth_provider_column.append(_p)
            #
            response.content = _soup.decode()
        except Exception as e:
            error(e)
        finally:
            return response

    def _login_link_for(self, org: Organization):
        _p = Tag(name="p")
        _a = Tag(name="a", attrs={
                "href": reverse('sentry-auth-organization',
                                kwargs={'organization_slug': org.slug}),
                "class": "btn btn-default btn-login-oidc",
                "style": "display: block"})
        _p.append(_a)
        #
        _span = Tag(name="span", attrs={"class": "provider-logo oidc"})
        _a.append(_span)
        _a.append(f'Sign to {org.name} with OIDC')
        return _p
