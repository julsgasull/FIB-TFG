import django
from django.conf import settings as django_settings
from django.utils.deprecation import MiddlewareMixin
from app.db import *

########################################################################


class SameSiteMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        django_support_samesite_none = django.VERSION[0] > 3 or (
            django.VERSION[0] == 3 and django.VERSION[1] >= 1
        )
        if request.is_secure() and not django_support_samesite_none:
            session_cookie_samesite = getattr(
                django_settings, "SESSION_COOKIE_SAMESITE", None
            )
            csrf_cookie_samesite = getattr(
                django_settings, "CSRF_COOKIE_SAMESITE", None
            )

            session_cookie_name = getattr(django_settings, "SESSION_COOKIE_NAME", None)
            csrf_cookie_name = getattr(django_settings, "CSRF_COOKIE_NAME", None)

            if (
                session_cookie_samesite is None
                and session_cookie_name in response.cookies
            ):
                response.cookies[session_cookie_name]["samesite"] = "None"
            if csrf_cookie_samesite is None and csrf_cookie_name in response.cookies:
                response.cookies[csrf_cookie_name]["samesite"] = "None"
        create_table_if_missing()
        return response


########################################################################
