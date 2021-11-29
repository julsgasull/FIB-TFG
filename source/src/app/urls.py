from django.conf import settings
from django.conf.urls import url
from django.urls import include, path
from .views import (
    login,
    launch,
    upload,
    consult,
    get_jwks,
    configure,
    score,
    scoreboard,
)

########################################################################

urlpatterns = [
    url(r"^login/$", login, name="app-login"),
    url(r"^launch/$", launch, name="app-launch"),
    url(r"^upload/$", upload, name="app-upload"),
    url(r"^consult/$", consult, name="app-consult"),
    url(r"^jwks/$", get_jwks, name="app-jwks"),
    url(
        r"^configure/(?P<launch_id>[\w-]+)/(?P<difficulty>[\w-]+)/$",
        configure,
        name="app-configure",
    ),
    url(
        r"^api/score/(?P<launch_id>[\w-]+)/(?P<earned_score>[\w-]+)/(?P<time_spent>[\w-]+)/$",
        score,
        name="app-api-score",
    ),
    url(
        r"^api/scoreboard/(?P<launch_id>[\w-]+)/$",
        scoreboard,
        name="app-api-scoreboard",
    ),
]

########################################################################

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

########################################################################
